git add .
git commit -m "Add two-factor authentication"
git push origin main

# Deploy to Cloud Run
cd ~/Globis-ROMS
git pull origin main
gcloud builds submit --tag us-central1-docker.pkg.dev/globis-hr/globis-repo/globis-hr:latest .
gcloud run deploy globis-hr --image us-central1-docker.pkg.dev/globis-hr/globis-repo/globis-hr:latest --region us-central1

# Run migrations
gcloud run jobs execute migrate-db --region=us-central1