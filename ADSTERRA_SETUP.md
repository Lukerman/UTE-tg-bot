# Adsterra Ads Integration Guide

This bot is pre-configured with ad placement slots for Adsterra monetization. Follow these steps to add your ad codes and start earning revenue from the redirect pages.

## 🎯 Ad Placement Summary

All 4 redirect pages (Step 1-4) include the following ad placements:

### Page 1, 2, 3 (Steps 1-3):
- ✅ **Popunder Ad** - Triggers when page loads
- ✅ **Banner Ad (Top)** - 728x90 banner above content
- ✅ **Native Banner** - Native ad format
- ✅ **Banner Ad (Bottom)** - 728x90 banner below content
- ✅ **Social Bar** - Bottom sticky social bar

### Page 4 (Final Step):
- ✅ **Smartlink Ad** - High-converting smart redirect
- ✅ **Banner Ad (Top)** - 728x90 banner
- ✅ **Native Banner** - Native ad format
- ✅ **Banner Ad (Bottom)** - 728x90 banner
- ✅ **Social Bar** - Bottom sticky social bar

## 📝 How to Add Your Adsterra Ad Codes

### Step 1: Get Your Adsterra Account
1. Sign up at [Adsterra.com](https://adsterra.com)
2. Verify your account
3. Add your website/Replit URL

### Step 2: Create Ad Units
In your Adsterra dashboard, create these ad units:
- **Popunder** (for page load monetization)
- **Banner 728x90** (for top/bottom banners)
- **Native Banner** (for native ads)
- **Smartlink** (for page 4)
- **Social Bar** (for sticky bottom bar)

### Step 3: Copy Ad Codes
For each ad unit you create, Adsterra will give you code like:
```html
<script type="text/javascript">
    atOptions = {
        'key' : 'abc123xyz456',
        'format' : 'iframe',
        'height' : 90,
        'width' : 728,
        'params' : {}
    };
</script>
<script type="text/javascript" src="//www.highperformanceformat.com/abc123xyz456/invoke.js"></script>
```

### Step 4: Edit web.py File

Open `web.py` and find the ad placement comments:

#### For Popunder Ads (in <head> section):
Find:
```html
<!-- Adsterra Popunder Ad -->
<script type="text/javascript">
    // Add your Adsterra Popunder code here
```

Replace with your popunder code:
```html
<!-- Adsterra Popunder Ad -->
<script type="text/javascript">
    atOptions = {
        'key' : 'YOUR_POPUNDER_KEY',
        'format' : 'iframe',
        'height' : 90,
        'width' : 728,
        'params' : {}
    };
</script>
<script type="text/javascript" src="//www.highperformanceformat.com/YOUR_KEY/invoke.js"></script>
```

#### For Banner Ads:
Find:
```html
<!-- Banner Ad - Top -->
<div class="banner-ad">
    <!-- Add your Adsterra Banner code here -->
```

Replace the comment with your banner code.

#### For Native Banners:
Find:
```html
<!-- Native Banner Ad -->
<div class="native-ad">
    <!-- Add your Adsterra Native Banner code here -->
```

Replace with your native banner code.

#### For Social Bar (at end of <body>):
Find:
```html
<!-- Adsterra Social Bar -->
<script type="text/javascript">
    // Add your Adsterra Social Bar code here
```

Replace with your social bar code.

#### For Smartlink (Page 4 only):
Find in PAGE_4_TEMPLATE:
```html
<!-- Adsterra Smartlink -->
<script type="text/javascript">
    // Add your Adsterra Smartlink code here
```

Replace with your smartlink code.

## 💰 Expected Revenue

With all ad placements active, each file download generates:
- **1 Popunder view** (Pages 1-4) = 4 views
- **6 Banner impressions** (2 per page × 3 pages) = 6 impressions
- **4 Native Banner impressions** (1 per page)
- **1 Smartlink click** (Page 4)
- **4 Social Bar impressions** (1 per page)

**Total per download:** Multiple ad impressions across 4 pages = Maximum revenue potential!

## 🚀 Testing Your Ads

After adding your ad codes:

1. Save the `web.py` file
2. The server will automatically restart
3. Upload a test file to your bot
4. Click the monetized link
5. Go through all 4 pages to verify ads appear

## ⚠️ Important Notes

- **Ad Placement Rules:** Place ads exactly where the comments indicate
- **Don't Remove Containers:** Keep the `<div class="banner-ad">` containers
- **Test Mode:** Use Adsterra test mode first to avoid policy violations
- **Ad Blocking:** Some users may have ad blockers - this is normal
- **Revenue:** CPM rates vary by country and ad type

## 📊 Optimization Tips

1. **Use All Ad Types:** More ad placements = more revenue
2. **Test Different Formats:** Try different banner sizes
3. **Monitor Performance:** Check Adsterra analytics regularly
4. **Update Codes:** Refresh ad codes if performance drops
5. **Traffic Quality:** Higher quality traffic = better CPM rates

## 🔧 Troubleshooting

### Ads Not Showing?
- Check if ad codes are properly pasted
- Verify Adsterra account is approved
- Ensure your Replit URL is added to Adsterra
- Check browser console for JavaScript errors
- Disable ad blocker for testing

### Low Revenue?
- Ensure all ad slots are filled
- Check if ads are approved in Adsterra dashboard
- Try different ad formats
- Increase traffic quality
- Check geo-targeting settings

## 📈 Revenue Tracking

Your total revenue comes from:
1. **Bot CPM earnings** (from geolocation tracking)
2. **Adsterra earnings** (from ad impressions/clicks)

Check both:
- Bot stats: `/stats` command in Telegram
- Adsterra earnings: Adsterra dashboard

---

**Need Help?** Contact Adsterra support or check their documentation at [publishers.adsterra.com](https://publishers.adsterra.com/)
