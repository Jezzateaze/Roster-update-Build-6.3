# 🚀 SUPER SIMPLE iPhone Access - Jeremy's Rostering

## The Easiest Way (Just 3 Steps!)

### Step 1: Frontend on Vercel (2 minutes)
1. Go to [vercel.com](https://vercel.com)
2. Sign in with GitHub
3. Click "Import Git Repository"
4. Connect your GitHub repo with the app code
5. Set folder to `/frontend`
6. Click Deploy!
7. Vercel gives you a URL like: `jeremys-rostering.vercel.app`

### Step 2: Backend on Railway (2 minutes) 
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "Deploy from GitHub"
4. Choose your repo, set folder to `/backend`
5. Add MongoDB database (one click)
6. Railway gives you backend URL

### Step 3: Connect Them (1 minute)
1. In Vercel, add environment variable:
   - `REACT_APP_BACKEND_URL` = your Railway backend URL
2. Redeploy frontend
3. Done! 

## 📱 Your iPhone Link
You'll get: **https://jeremys-rostering.vercel.app**

Just bookmark it or add to home screen!

## 🎯 Why This is Easier
- **Vercel**: Made for React apps, auto-deploys
- **Railway**: Handles databases automatically  
- **No Docker needed**
- **No complex config**
- **Both have generous free tiers**

## 🔄 Auto-Updates
Every time you push code to GitHub:
- Vercel automatically updates your app
- Railway automatically updates your backend
- Zero maintenance!

## 💰 Cost
- **100% Free** for your needs
- Vercel: Free tier perfect for personal use
- Railway: $5/month free credits (plenty for this app)

---

**Ready to deploy? I can help you set this up step by step!**