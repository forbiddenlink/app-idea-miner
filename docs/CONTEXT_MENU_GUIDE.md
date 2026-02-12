# Context Menu Quick Test Guide 🎯

**Time:** 5 minutes
**URL:** http://localhost:3000

---

## What Are Context Menus?

Right-click (or Ctrl+Click on Mac) any **Cluster Card** or **Idea Card** to reveal a powerful quick-actions menu with shortcuts for common tasks.

---

## Test 1: Cluster Context Menu (2 min)

### Step 1: Open Clusters Page
1. Navigate to http://localhost:3000/clusters
2. Find any cluster card

### Step 2: Right-Click Menu
1. **Right-click** (or Ctrl+Click) on a cluster card
2. ✅ **Expected:** Context menu appears with:
   - 📋 Copy Cluster Name
   - 🔗 Copy URL (⌘C)
   - 🔗 Share
   - ❤️ Add to Favorites (or Remove from Favorites if already favorited)
   - 📄 Open in New Tab (⌘↵)

### Step 3: Test Each Action

**Copy Cluster Name:**
1. Click "Copy Cluster Name"
2. Open a text editor
3. Paste (Cmd+V)
4. ✅ **Expected:** Cluster name appears

**Copy URL:**
1. Right-click cluster again
2. Click "Copy URL"
3. Paste in address bar
4. ✅ **Expected:** URL like `http://localhost:3000/clusters/xxx`

**Share:**
1. Right-click cluster
2. Click "Share"
3. ✅ **Expected:**
   - macOS/iOS: Native share sheet appears
   - Windows/Linux: URL copied to clipboard (fallback)

**Add to Favorites:**
1. Right-click a non-favorited cluster
2. Click "Add to Favorites"
3. ✅ **Expected:**
   - Heart icon turns solid red
   - Next right-click shows "Remove from Favorites"

**Open in New Tab:**
1. Right-click cluster
2. Click "Open in New Tab"
3. ✅ **Expected:** Cluster detail page opens in new browser tab

---

## Test 2: Idea Context Menu (2 min)

### Step 1: Open Ideas Page
1. Navigate to http://localhost:3000/ideas
2. Find any idea card

### Step 2: Right-Click Menu
1. **Right-click** on an idea card
2. ✅ **Expected:** Context menu appears with:
   - 📋 Copy Problem Statement
   - 🔗 Copy URL
   - 🔗 View Original Source (if available)
   - 🔗 Share

### Step 3: Test Actions

**Copy Problem Statement:**
1. Click "Copy Problem Statement"
2. Paste in text editor
3. ✅ **Expected:** Full problem statement text appears

**View Original Source:**
1. Find an idea with a source URL (from HackerNews, Reddit, etc.)
2. Right-click
3. Click "View Original Source"
4. ✅ **Expected:** Original post opens in new tab

---

## Test 3: Menu Behavior (1 min)

### Close Menu
1. Right-click to open menu
2. Press **Escape** key
3. ✅ **Expected:** Menu closes smoothly

### Click Outside
1. Right-click to open menu
2. Click anywhere else on page
3. ✅ **Expected:** Menu closes

### Viewport Edge Handling
1. Right-click a card in the **top-right** corner
2. ✅ **Expected:** Menu adjusts position to stay in viewport
3. Right-click a card in the **bottom-right**
4. ✅ **Expected:** Menu appears above cursor if needed

### Animation
1. Right-click any card
2. ✅ **Expected:** Menu fades in with scale animation (0.1s)

---

## Keyboard Shortcuts

All context menu items support keyboard shortcuts:

- **Cmd+C** - Copy URL (if menu is open)
- **Cmd+Enter** - Open in new tab
- **Escape** - Close menu

---

## Visual Design

### Menu Appearance
- ✅ Glassmorphism background (slate-800/95)
- ✅ Backdrop blur effect
- ✅ Rounded corners (border-radius: 12px)
- ✅ Shadow: 2xl
- ✅ Border: slate-700/50

### Menu Items
- ✅ Icon on left (4x4)
- ✅ Text in middle
- ✅ Keyboard shortcut on right (if applicable)
- ✅ Hover: Background changes to slate-700/50
- ✅ Hover: Left padding increases (pl-5)
- ✅ Disabled items: 50% opacity, no hover

### Colors
- ✅ Default: text-slate-300
- ✅ Hover: hover:bg-slate-700/50
- ✅ Danger items: text-red-400, hover:bg-red-500/10

---

## Common Issues

### Menu Doesn't Appear
- **Check:** Are you right-clicking directly on the card?
- **Fix:** Ensure you're not clicking on a link or button inside the card

### Menu Cut Off
- **Check:** Is it near viewport edge?
- **Expected:** Should auto-adjust position

### Context Menu Blocked
- **Check:** Browser might be blocking right-click
- **Fix:** Use Ctrl+Click as alternative on Mac

### Actions Don't Work
- **Check:** Console for errors (F12)
- **Check:** Clipboard permissions for copy actions

---

## Browser Compatibility

### Tested Browsers
- ✅ Chrome 121+ (full support)
- ✅ Safari 17+ (full support, native share on macOS)
- ✅ Firefox 120+ (full support)
- ✅ Edge 121+ (full support)

### Share API Support
- **Native Share Sheet:** Safari (macOS/iOS), Chrome (Android)
- **Fallback:** Copy to clipboard on unsupported browsers

### Clipboard API
- **Requirements:** HTTPS or localhost
- **Fallback:** Manual copy if permissions denied

---

## Accessibility

### Screen Reader Support
- Menu items announced with role="menuitem"
- Keyboard navigation with Tab
- Escape to close
- Focus trapped within menu

### Keyboard-Only Navigation
1. Tab to cluster card
2. Press **Application key** (or Shift+F10)
3. Menu opens
4. Arrow keys to navigate
5. Enter to select
6. Escape to close

---

## Developer Console

### Successful Copy
```
Cluster name copied to clipboard
URL copied to clipboard
Problem statement copied to clipboard
```

### Share Action
```
// Native share
navigator.share() called

// Fallback
URL copied to clipboard
```

---

## Next Steps

After testing context menus:

1. ✅ Test all 5 Phase 8E features (35 min)
2. 📊 Track usage metrics
3. 📝 Gather user feedback
4. 🚀 Deploy to production

---

## Quick Reference

**Open Menu:** Right-click (or Ctrl+Click)
**Close Menu:** Escape, click outside, or select action
**Copy Actions:** Automatically copy to clipboard
**Share Action:** Native share sheet or clipboard fallback
**New Tab:** Opens cluster/idea in new browser tab

**Need help?** Check `/docs/PHASE_8E_COMPLETE.md` for full testing guide.

---

**Happy Testing!** 🎉
