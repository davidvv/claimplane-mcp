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

import { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, Edit2, Plane, MapPin, Calendar, User, Hash } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import type { BoardingPassData, BoardingPassDataWithConfidence } from '@/types/api';

interface ExtractedDataPreviewProps {
  data: BoardingPassData;
  confidence: BoardingPassDataWithConfidence;
  overallConfidence: number;
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

// Confidence badge helper
function ConfidenceBadge({ confidence }: { confidence: number }) {
  if (confidence >= 0.8) {
    return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800">
      <CheckCircle2 className="w-3 h-3 mr-1" />
      High confidence
    </Badge>;
  } else if (confidence >= 0.5) {
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
  confidence,
  overallConfidence,
  onConfirm,
  onRetry,
  isLoading = false,
}: ExtractedDataPreviewProps) {
  const parsedName = parseName(data.passengerName);
  
  const [editMode, setEditMode] = useState(false);
  const [editedData, setEditedData] = useState<EditedBoardingPassData>({
    flightNumber: data.flightNumber || '',
    departureAirport: data.departureAirport || '',
    arrivalAirport: data.arrivalAirport || '',
    flightDate: data.flightDate || '',
    firstName: parsedName.firstName,
    lastName: parsedName.lastName,
    bookingReference: data.bookingReference || '',
  });

  // Update edited data when OCR data changes
  useEffect(() => {
    const parsedName = parseName(data.passengerName);
    setEditedData({
      flightNumber: data.flightNumber || '',
      departureAirport: data.departureAirport || '',
      arrivalAirport: data.arrivalAirport || '',
      flightDate: data.flightDate || '',
      firstName: parsedName.firstName,
      lastName: parsedName.lastName,
      bookingReference: data.bookingReference || '',
    });
  }, [data]);

  const handleConfirm = () => {
    onConfirm(editedData);
  };

  const hasLowConfidenceFields = overallConfidence < 0.6;

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
            <ConfidenceBadge confidence={overallConfidence} />
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
                {confidence.flightNumber && (
                  <ConfidenceBadge confidence={confidence.flightNumber.confidence} />
                )}
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
                {confidence.flightDate && (
                  <ConfidenceBadge confidence={confidence.flightDate.confidence} />
                )}
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
                {confidence.departureAirport && (
                  <ConfidenceBadge confidence={confidence.departureAirport.confidence} />
                )}
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
                {confidence.arrivalAirport && (
                  <ConfidenceBadge confidence={confidence.arrivalAirport.confidence} />
                )}
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
                {confidence.passengerName && (
                  <ConfidenceBadge confidence={confidence.passengerName.confidence} />
                )}
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
                {confidence.bookingReference && (
                  <ConfidenceBadge confidence={confidence.bookingReference.confidence} />
                )}
              </div>
            </div>
          </div>
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
