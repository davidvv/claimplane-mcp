/**
 * ExtractedDataPreview Component
 * 
 * Displays OCR-extracted data from boarding pass with:
 * - Confidence score indicators
 * - Editable fields for corrections
 * - Name split confirmation (SURNAME/FIRSTNAME)
 * - Low-confidence warnings
 * - Actions: Use Data, Try Another Image
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, Edit2, Plane, User, ArrowLeftRight } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import type { BoardingPassData, FieldConfidenceScores, FlightSegment } from '@/types/api';

interface ExtractedDataPreviewProps {
  data: BoardingPassData;
  fieldConfidence: FieldConfidenceScores;
  confidenceScore: number;
  onConfirm: (editedData: EditedBoardingPassData) => void;
  onRetry: () => void;
  isLoading?: boolean;
}

export interface EditedBoardingPassData {
  flightNumber: string;
  departureAirport: string;
  arrivalAirport: string;
  flightDate: string;
  firstName: string;
  lastName: string;
  bookingReference?: string;
  flights?: FlightSegment[];
}

// Parse "SURNAME/FIRSTNAME" format
function parseName(passengerName?: string | null): { firstName: string; lastName: string } {
  if (!passengerName) return { firstName: '', lastName: '' };

  // Common formats: "SURNAME/FIRSTNAME", "LASTNAME FIRSTNAME", "LASTNAME, FIRSTNAME"
  if (passengerName.includes('/')) {
    const [lastName, firstName] = passengerName.split('/').map(s => s.trim());
    return {
      firstName: firstName || '',
      lastName: lastName || '',
    };
  } else if (passengerName.includes(',')) {
    const [lastName, firstName] = passengerName.split(',').map(s => s.trim());
    return {
      firstName: firstName || '',
      lastName: lastName || '',
    };
  } else {
    // Assume "FIRSTNAME LASTNAME" or single name
    const parts = passengerName.trim().split(/\s+/);
    if (parts.length >= 2) {
      return {
        firstName: parts[0],
        lastName: parts.slice(1).join(' '),
      };
    } else {
      return {
        firstName: parts[0] || '',
        lastName: '',
      };
    }
  }
}

// Check if name might need verification (multi-word names)
function hasMultiWordName(firstName: string, lastName: string): boolean {
  const totalWords = (firstName.split(/\s+/).length || 0) + (lastName.split(/\s+/).length || 0);
  return totalWords >= 3;
}

// Confidence badge helper - now accepts optional fallback for when field confidence is unavailable
function ConfidenceBadge({ confidence, fallback }: { confidence?: number | null; fallback?: number }) {
  // Use fallback (overall confidence) when field confidence is null/undefined
  const effectiveConfidence = confidence ?? fallback ?? 0;
  
  if (effectiveConfidence >= 0.8) {
    return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800">
      <CheckCircle2 className="w-3 h-3 mr-1" />
      High confidence
    </Badge>;
  } else if (effectiveConfidence >= 0.5) {
    return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800">
      <AlertTriangle className="w-3 h-3 mr-1" />
      Medium confidence
    </Badge>;
  } else {
    return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800">
      <AlertTriangle className="w-3 h-3 mr-1" />
      Low confidence
    </Badge>;
  }
}

export function ExtractedDataPreview({
  data,
  fieldConfidence,
  confidenceScore,
  onConfirm,
  onRetry,
  isLoading = false,
}: ExtractedDataPreviewProps) {
  // Group flights by tripIndex to identify separate trips (outbound vs return)
  const trips = React.useMemo(() => {
    if (!data.flights?.length) return [];
    
    const tripMap = new Map<number, typeof data.flights>();
    data.flights.forEach(flight => {
      const tripIdx = flight.tripIndex ?? 1;
      if (!tripMap.has(tripIdx)) tripMap.set(tripIdx, []);
      tripMap.get(tripIdx)!.push(flight);
    });
    
    return Array.from(tripMap.entries())
      .sort(([a], [b]) => a - b)
      .map(([tripIndex, flights]) => ({
        tripIndex,
        flights,
        // Use first flight of trip for display
        mainFlight: flights[0],
        label: flights[0]?.legType?.includes('return') ? 'Return Flight' : 'Outbound Flight',
      }));
  }, [data.flights]);

  const hasMultipleTrips = trips.length > 1;
  
  // State for selected trip (default to first trip)
  const [selectedTripIndex, setSelectedTripIndex] = useState(1);
  
  // Get selected trip's main flight
  const selectedTrip = trips.find(t => t.tripIndex === selectedTripIndex) || trips[0];
  const selectedFlight = selectedTrip?.mainFlight;
  
  const firstPassenger = data.passengers?.[0];
  
  // Use selected flight data (or fallback to flat fields)
  const effectiveFlightNumber = selectedFlight?.flightNumber || data.flightNumber || '';
  const effectiveDepartureAirport = selectedFlight?.departureAirport || data.departureAirport || '';
  const effectiveArrivalAirport = selectedFlight?.arrivalAirport || data.arrivalAirport || '';
  const effectiveFlightDate = selectedFlight?.departureDate || data.flightDate || '';
  const effectiveBookingReference = data.bookingReference || firstPassenger?.bookingReference || '';
  
  // For passenger name, prefer passengers array, then fall back to passengerName field
  const effectiveFirstName = firstPassenger?.firstName || '';
  const effectiveLastName = firstPassenger?.lastName || '';
  const parsedName = (effectiveFirstName || effectiveLastName) 
    ? { firstName: effectiveFirstName, lastName: effectiveLastName }
    : parseName(data.passengerName);

  // Count for multi-passenger display
  const passengerCount = data.passengers?.length || (data.passengerName ? 1 : 0);

  const [editMode, setEditMode] = useState(false);
  const [editedData, setEditedData] = useState<EditedBoardingPassData>({
    flightNumber: effectiveFlightNumber,
    departureAirport: effectiveDepartureAirport,
    arrivalAirport: effectiveArrivalAirport,
    flightDate: effectiveFlightDate,
    firstName: parsedName.firstName,
    lastName: parsedName.lastName,
    bookingReference: effectiveBookingReference,
    flights: selectedTrip?.flights,
  });

  // Update edited data when OCR data or selected trip changes
  useEffect(() => {
    const selectedTrip = trips.find(t => t.tripIndex === selectedTripIndex) || trips[0];
    const selectedFlight = selectedTrip?.mainFlight;
    const firstPassenger = data.passengers?.[0];
    
    const effectiveFlightNumber = selectedFlight?.flightNumber || data.flightNumber || '';
    const effectiveDepartureAirport = selectedFlight?.departureAirport || data.departureAirport || '';
    const effectiveArrivalAirport = selectedFlight?.arrivalAirport || data.arrivalAirport || '';
    const effectiveFlightDate = selectedFlight?.departureDate || data.flightDate || '';
    const effectiveBookingReference = data.bookingReference || firstPassenger?.bookingReference || '';
    
    const effectiveFirstName = firstPassenger?.firstName || '';
    const effectiveLastName = firstPassenger?.lastName || '';
    const parsedName = (effectiveFirstName || effectiveLastName) 
      ? { firstName: effectiveFirstName, lastName: effectiveLastName }
      : parseName(data.passengerName);

    setEditedData({
      flightNumber: effectiveFlightNumber,
      departureAirport: effectiveDepartureAirport,
      arrivalAirport: effectiveArrivalAirport,
      flightDate: effectiveFlightDate,
      firstName: parsedName.firstName,
      lastName: parsedName.lastName,
      bookingReference: effectiveBookingReference,
      flights: selectedTrip?.flights,
    });
  }, [data, selectedTripIndex, trips]);

  const handleConfirm = () => {
    onConfirm(editedData);
  };

  const hasLowConfidenceFields = confidenceScore < 0.6;

  return (
    <Card className="border-2 border-blue-500">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              Data Extracted Successfully
            </CardTitle>
            <CardDescription>
              Review the extracted information and make corrections if needed
            </CardDescription>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground mb-1">Overall Confidence</p>
            <ConfidenceBadge confidence={confidenceScore} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Warning for low confidence */}
        {hasLowConfidenceFields && (
          <div className="rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 p-4">
            <div className="flex gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-yellow-900 dark:text-yellow-200">
                  Please verify the extracted data
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  Some fields have low confidence scores. Please review and correct any errors before continuing.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Multi-passenger notification */}
        {passengerCount > 1 && (
          <div className="rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 p-4">
            <div className="flex gap-2">
              <User className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-200">
                  Group booking detected
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Found <strong>{passengerCount} passengers</strong>.
                  Showing primary passenger below. All passengers will be added in Step 3.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Multi-trip flight selector (round-trip / multi-city) */}
        {hasMultipleTrips && (
          <div className="rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 p-4">
            <div className="flex gap-2">
              <ArrowLeftRight className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-amber-900 dark:text-amber-200 mb-2">
                  Multiple trips detected - Select the flight to claim
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
                  This booking contains {trips.length} separate trips. Please select which flight was delayed or cancelled.
                </p>
                <div className="grid gap-2">
                  {trips.map((trip) => (
                    <button
                      key={trip.tripIndex}
                      type="button"
                      onClick={() => setSelectedTripIndex(trip.tripIndex)}
                      className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${
                        selectedTripIndex === trip.tripIndex
                          ? 'border-amber-500 bg-amber-100 dark:bg-amber-900/30'
                          : 'border-gray-200 dark:border-gray-700 hover:border-amber-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {trip.mainFlight?.flightNumber}
                          </span>
                          <span className="mx-2 text-gray-500">|</span>
                          <span className="text-gray-700 dark:text-gray-300">
                            {trip.mainFlight?.departureAirport} → {trip.mainFlight?.arrivalAirport}
                          </span>
                          <span className="mx-2 text-gray-500">|</span>
                          <span className="text-gray-600 dark:text-gray-400">
                            {trip.mainFlight?.departureDate}
                          </span>
                        </div>
                        <Badge variant="outline" className={
                          trip.mainFlight?.legType?.includes('return')
                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                            : 'bg-green-50 text-green-700 border-green-200'
                        }>
                          {trip.label}
                        </Badge>
                      </div>
                      {trip.flights.length > 1 && (
                        <p className="text-xs text-gray-500 mt-1">
                          + {trip.flights.length - 1} connecting flight{trip.flights.length > 2 ? 's' : ''}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Mode Toggle */}
        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setEditMode(!editMode)}
          >
            <Edit2 className="w-4 h-4 mr-2" />
            {editMode ? 'View Mode' : 'Edit Mode'}
          </Button>
        </div>

        {/* Flight Information */}
        <div className="space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Plane className="w-4 h-4" />
            Flight Information
          </h3>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Flight Number */}
            <div>
              <Label htmlFor="edit-flight-number">Flight Number</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-flight-number"
                    value={editedData.flightNumber}
                    onChange={(e) => setEditedData({ ...editedData, flightNumber: e.target.value.toUpperCase() })}
                    className="flex-1"
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.flightNumber || '-'}</p>
                )}
                <ConfidenceBadge confidence={fieldConfidence.flightNumber} fallback={confidenceScore} />
              </div>
            </div>

            {/* Flight Date */}
            <div>
              <Label htmlFor="edit-flight-date">Flight Date</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-flight-date"
                    type="date"
                    value={editedData.flightDate}
                    onChange={(e) => setEditedData({ ...editedData, flightDate: e.target.value })}
                    className="flex-1"
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.flightDate || '-'}</p>
                )}
                <ConfidenceBadge confidence={fieldConfidence.flightDate} fallback={confidenceScore} />
              </div>
            </div>

            {/* Departure Airport */}
            <div>
              <Label htmlFor="edit-departure">Departure Airport</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-departure"
                    value={editedData.departureAirport}
                    onChange={(e) => setEditedData({ ...editedData, departureAirport: e.target.value.toUpperCase() })}
                    className="flex-1"
                    maxLength={3}
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.departureAirport || '-'}</p>
                )}
                <ConfidenceBadge confidence={fieldConfidence.departureAirport} fallback={confidenceScore} />
              </div>
            </div>

            {/* Arrival Airport */}
            <div>
              <Label htmlFor="edit-arrival">Arrival Airport</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-arrival"
                    value={editedData.arrivalAirport}
                    onChange={(e) => setEditedData({ ...editedData, arrivalAirport: e.target.value.toUpperCase() })}
                    className="flex-1"
                    maxLength={3}
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.arrivalAirport || '-'}</p>
                )}
                <ConfidenceBadge confidence={fieldConfidence.arrivalAirport} fallback={confidenceScore} />
              </div>
            </div>
          </div>
        </div>

        {/* Passenger Information */}
        <div className="space-y-4 pt-4 border-t">
          <h3 className="font-semibold flex items-center gap-2">
            <User className="w-4 h-4" />
            Passenger Information
          </h3>

          <div className="grid md:grid-cols-2 gap-4">
            {/* First Name */}
            <div>
              <Label htmlFor="edit-first-name">First Name</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-first-name"
                    value={editedData.firstName}
                    onChange={(e) => setEditedData({ ...editedData, firstName: e.target.value })}
                    className="flex-1"
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.firstName || '-'}</p>
                )}
                <ConfidenceBadge confidence={fieldConfidence.passengerName} fallback={confidenceScore} />
              </div>
            </div>

            {/* Last Name */}
            <div>
              <Label htmlFor="edit-last-name">Last Name</Label>
              <div className="flex items-center gap-2">
                {editMode ? (
                  <Input
                    id="edit-last-name"
                    value={editedData.lastName}
                    onChange={(e) => setEditedData({ ...editedData, lastName: e.target.value })}
                    className="flex-1"
                  />
                ) : (
                  <p className="text-lg font-medium">{editedData.lastName || '-'}</p>
                )}
              </div>
              {data.passengerName && (
                <p className="text-xs text-muted-foreground mt-1">
                  Original: {data.passengerName}
                </p>
              )}
            </div>

            {/* Booking Reference */}
             <div>
               <Label htmlFor="edit-booking-ref">Booking Reference (PNR)</Label>
               <div className="flex items-center gap-2">
                 {editMode ? (
                   <Input
                     id="edit-booking-ref"
                     value={editedData.bookingReference}
                     onChange={(e) => setEditedData({ ...editedData, bookingReference: e.target.value.toUpperCase() })}
                     className="flex-1"
                   />
                 ) : (
                   <p className="text-lg font-medium">{editedData.bookingReference || '-'}</p>
                 )}
                 <ConfidenceBadge confidence={fieldConfidence.bookingReference} fallback={confidenceScore} />
               </div>
             </div>
           </div>

           {/* Warning for Multi-Word Names */}
           {hasMultiWordName(editedData.firstName, editedData.lastName) && (
             <div className="rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 p-4 mt-4">
               <div className="flex gap-2">
                 <AlertTriangle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                 <div>
                   <p className="font-medium text-blue-900 dark:text-blue-200">
                     Please verify the name split
                   </p>
                   <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                     We detected multiple words in your name (common for Spanish, Portuguese, Dutch, German, and French surnames). 
                     Please check that the First Name and Last Name are split correctly. You can edit them above if needed.
                   </p>
                 </div>
               </div>
             </div>
           )}
         </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1"
          >
            Use This Data
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onRetry}
            disabled={isLoading}
          >
            Try Another Image
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
