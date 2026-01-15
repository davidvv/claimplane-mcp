# Google Cloud Vision API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your Project ID

## Step 2: Enable Vision API

1. Go to [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com)
2. Click **"Enable"**
3. Wait for activation (usually 1-2 minutes)

## Step 3: Create Service Account

1. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click **"Create Service Account"**
3. Fill in details:
   - **Name**: `easyairclaim-ocr`
   - **Description**: `OCR service for boarding pass extraction`
4. Click **"Create and Continue"**
5. Grant role: **Cloud Vision API User** (or Editor for development)
6. Click **"Done"**

## Step 4: Download Credentials

1. Find your service account in the list
2. Click the **⋮** menu → **Manage keys**
3. Click **"Add Key"** → **"Create new key"**
4. Choose **JSON** format
5. Click **"Create"**
6. Save the downloaded JSON file securely

## Step 5: Configure Application

### Option A: Docker (Recommended)

1. Copy the JSON key file to your project:
```bash
cp ~/Downloads/easyairclaim-ocr-*.json /home/david/easyAirClaim/easyAirClaim/google-cloud-key.json
```

2. Update `docker-compose.yml` to mount the credentials:
```yaml
services:
  api:
    environment:
      GOOGLE_APPLICATION_CREDENTIALS: /app/google-cloud-key.json
    volumes:
      - ./google-cloud-key.json:/app/google-cloud-key.json:ro
```

3. Add to `.gitignore`:
```bash
echo "google-cloud-key.json" >> .gitignore
```

### Option B: Environment Variable

1. Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
```

2. Add to `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-cloud-key.json
```

## Step 6: Verify Setup

Test the credentials:

```bash
docker exec flight_claim_api python -c "
from google.cloud import vision
client = vision.ImageAnnotatorClient()
print('✓ Google Vision API configured successfully!')
"
```

## Pricing

- **Free tier**: 1,000 images/month
- **Beyond free tier**: $1.50 per 1,000 images
- **Document Text Detection**: Same rate

### Cost Examples

| Monthly Volume | Cost |
|----------------|------|
| 1,000 images | **FREE** |
| 5,000 images | $6.00 |
| 10,000 images | $13.50 |
| 50,000 images | $73.50 |

With barcode reading as first priority, many boarding passes will be FREE (barcode extraction).

## Security Best Practices

1. **Never commit the JSON key file** to git
2. **Restrict service account permissions** to only Vision API
3. **Rotate keys regularly** (every 90 days)
4. **Use separate keys** for development and production
5. **Monitor API usage** in Cloud Console

## Troubleshooting

### Error: "Could not load default credentials"

**Solution**: Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly:
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

### Error: "API has not been enabled"

**Solution**: Enable Vision API in Cloud Console:
```bash
gcloud services enable vision.googleapis.com --project=YOUR_PROJECT_ID
```

### Error: "Permission denied"

**Solution**: Grant Vision API User role to service account:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:easyairclaim-ocr@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudvision.user"
```

### Error: "Quota exceeded"

**Solution**: Check your quota usage:
- Go to [Quotas](https://console.cloud.google.com/iam-admin/quotas)
- Filter by "Vision API"
- Request quota increase if needed

## Monitoring Usage

Track your API usage:
1. Go to [Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Dashboard**
3. Select **Cloud Vision API**
4. View usage graphs and metrics

## Next Steps

After setup:
1. Rebuild Docker container: `docker compose build api`
2. Restart services: `docker compose up -d api`
3. Test with boarding pass upload
4. Monitor logs: `docker logs flight_claim_api -f`

## Support

- [Vision API Documentation](https://cloud.google.com/vision/docs)
- [Pricing Details](https://cloud.google.com/vision/pricing)
- [Client Library (Python)](https://googleapis.dev/python/vision/latest/)
