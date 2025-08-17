# Jeremy's Rostering - Railway Deployment Guide

## 🎯 Goal
Deploy your Shift Roster & Pay Calculator app to Railway (free hosting) so you can access it from your iPhone with just one click!

## 📋 What We're Deploying
- **React Frontend** - Your roster calendar and management interface
- **FastAPI Backend** - All the pay calculations and data management  
- **MongoDB Database** - Stores all your staff, shifts, and settings

## 🚀 Step-by-Step Deployment

### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account (it's free!)
3. Verify your email if needed

### Step 2: Set Up GitHub Repository
1. Go to GitHub.com and create a new repository called "jeremys-rostering"
2. Make it public (required for free Railway hosting)
3. We'll upload your app code there

### Step 3: Deploy Backend (FastAPI + MongoDB)
1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your "jeremys-rostering" repository
4. Select the `/backend` folder as the root directory
5. Railway will automatically detect it's a Python app and deploy it

### Step 4: Add MongoDB Database
1. In your Railway project, click "Add Service"
2. Select "Database" → "MongoDB"
3. Railway will create a free MongoDB instance
4. Copy the MongoDB connection URL from the database service

### Step 5: Configure Backend Environment
1. Go to your backend service in Railway
2. Click on "Variables" tab
3. Add these environment variables:
   - `MONGO_URL` = [the MongoDB URL from step 4]
   - `DB_NAME` = shift_roster_db
   - `CORS_ORIGINS` = *

### Step 6: Deploy Frontend (React)
1. In Railway, add another service to your project
2. Select "Deploy from GitHub repo" again
3. Choose your same repository
4. Select the `/frontend` folder as the root directory
5. Railway will detect it's a React app and build it

### Step 7: Configure Frontend Environment
1. Go to your frontend service in Railway
2. Click on "Variables" tab
3. Add this environment variable:
   - `REACT_APP_BACKEND_URL` = [your backend service URL from Railway]

### Step 8: Generate Public URLs
1. For both services, go to Settings → Networking
2. Click "Generate Domain" for each service
3. Your app will be accessible at something like:
   - Frontend: `https://jeremys-rostering-frontend.railway.app`
   - Backend: `https://jeremys-rostering-backend.railway.app`

## 📱 Your iPhone Link
Once deployed, you'll get a URL like:
**https://jeremys-rostering.railway.app**

Just bookmark this link or add it to your iPhone home screen!

## 🔧 Files Created for Deployment
- `backend/Dockerfile` - Instructions for Railway to run your backend
- `frontend/Dockerfile` - Instructions for Railway to run your frontend  
- `railway.json` - Railway configuration
- This guide!

## 💡 Next Steps
1. I'll help you upload the code to GitHub
2. Follow the Railway deployment steps above
3. Test your app on iPhone
4. Enjoy your one-click roster management!

## 🆘 Need Help?
The Railway documentation is excellent: https://docs.railway.app/
Or let me know if you run into any issues!