# Phase 8E Testing Guide

## Quick Test Checklist

### Prerequisites
```bash
# Make sure backend is running
cd /Users/elizabethstein/Projects/app-idea-miner
make dev

# In another terminal, start frontend
cd apps/web
npm run dev
```

---

## Test 1: Favorites System (2 minutes)

### Steps
1. Open http://localhost:3000
2. Navigate to **Clusters** page
3. Find a cluster card
4. **Look for heart icon** in top-right corner (should be outline)
5. **Click the heart**
   - ✅ Should turn solid red
   - ✅ Should not navigate to cluster detail
6. **Refresh page** (Cmd+R / Ctrl+R)
   - ✅ Heart should still be solid red
7. **Click heart again**
   - ✅ Should turn back to outline
8. **Hover over heart**
   - ✅ Tooltip should appear: "Add to favorites"

### Expected Behavior
- Heart animates smoothly on click
- Favorite state persists across refreshes
- No errors in console
- Clicking heart doesn't navigate away

### If It Fails
- Check browser console for errors
- Verify localStorage is enabled
- Check Network tab for failed requests (should be none)

---

## Test 2: Enhanced Tooltips (2 minutes)

### Steps
1. Still on **Clusters** page
2. Find the **idea count** metric (person icon + number)
3. **Hover over it for 0.5 seconds**
   - ✅ Rich tooltip should appear
   - ✅ Should show: "Idea Count" title
   - ✅ Should show: Description text
   - ✅ Should show: Metrics (Total Ideas, Quality)
4. **Move mouse away**
   - ✅ Tooltip should disappear
5. **Hover over sentiment metric** (emoji + percentage)
   - ✅ Should show sentiment details
6. **Hover near screen edge**
   - ✅ Tooltip should stay within viewport

### Expected Behavior
- Tooltip appears after ~200ms delay
- Tooltip has glassmorphism styling
- Tooltip shows detailed metrics
- No tooltip flicker

### If It Fails
- Check if pointer-events are blocking
- Verify Framer Motion is loaded
- Check z-index conflicts

---

## Test 3: Filter Chips (3 minutes)

### Steps
1. On **Clusters** page
2. Open **filter sidebar** (left side)
3. **Change sort to "trend"**
   - ✅ Filter chip should appear: "Sort By: trend"
4. **Set min size to 5**
   - ✅ Another chip should appear: "Min Size: 5"
5. **Enter search term "budget"** and press Enter
   - ✅ Third chip should appear: "Search: budget"
6. **Click X on one chip**
   - ✅ Chip should animate out
   - ✅ Filter should be removed
   - ✅ Results should update
7. **Click "Clear All"**
   - ✅ All chips should disappear
   - ✅ Filters should reset to defaults

### Expected Behavior
- Chips appear above cluster grid
- Each chip has X button
- Chips animate in/out smoothly
- URL params update on changes

### If It Fails
- Check URL params are being set
- Verify FilterChips component is imported
- Check buildChips logic

---

## Test 4: Command Palette (3 minutes)

### Steps
1. From any page
2. **Press Cmd+K** (Mac) or **Ctrl+K** (Windows)
   - ✅ Modal should open
   - ✅ Search input should be focused
3. **Type "dashboard"**
   - ✅ Should see "Dashboard" result
4. **Type "budget"**
   - ✅ Should see clusters/ideas about budgeting
5. **Press Escape**
   - ✅ Modal should close
6. **Look at navbar top-right**
   - ✅ Should see "⌘K" button
7. **Click ⌘K button**
   - ✅ Should open command palette
8. **Click backdrop (outside modal)**
   - ✅ Should close palette

### Expected Behavior
- Opens instantly on Cmd+K
- Search filters results in real-time
- Clicking result navigates and closes palette
- Recent searches show when empty

### If It Fails
- Check keyboard event listeners
- Verify HeadlessUI Dialog is working
- Check React Router navigation

---

## Test 5: Integration Test (5 minutes)

### Scenario: Full User Flow
1. **Start on Dashboard**
2. **Press Cmd+K** → Search "reading" → Click result
   - Should navigate to cluster
3. **Click heart to favorite** the cluster
   - Heart should turn red
4. **Press Alt+C** (keyboard shortcut)
   - Should go to Clusters page
5. **Filter by min size 3** + **Sort by sentiment**
   - Should see 2 filter chips
6. **Hover over metrics** on cards
   - Should see tooltips with details
7. **Click X on one filter chip**
   - Filter should clear, results update
8. **Press Cmd+H** (keyboard shortcut)
   - Should return to Dashboard
9. **Refresh page**
   - Favorite should still be red
10. **Press Cmd+K** → Type recent search
    - Should show in "Recent Searches" section

### Expected Flow
- All features work together seamlessly
- No console errors
- Smooth animations throughout
- Keyboard shortcuts work globally

---

## Performance Test (2 minutes)

### Steps
1. Open browser DevTools (F12)
2. Go to **Performance** tab
3. Click **Record**
4. Do the following actions:
   - Click 5 favorites
   - Hover over 5 tooltips
   - Add 3 filters
   - Open command palette
   - Search for "budget"
5. **Stop recording**

### Check
- ✅ **No long tasks** (> 50ms)
- ✅ **Smooth 60fps** animations
- ✅ **Layout shifts** minimal
- ✅ **Memory usage** stable

### Benchmarks
- Command palette open: < 100ms
- Tooltip render: < 16ms (1 frame)
- Filter chip render: < 16ms
- Favorite toggle: < 10ms

---

## Browser Compatibility Test (5 minutes)

### Test In
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile Safari (iOS)
- ✅ Mobile Chrome (Android)

### What to Test
1. Cmd+K opens on Mac
2. Ctrl+K opens on Windows/Linux
3. Tooltips work on desktop
4. Favorites persist
5. Filter chips display correctly
6. Responsive design intact

---

## Accessibility Test (3 minutes)

### Tools
- Browser: Chrome DevTools Lighthouse
- Screen Reader: VoiceOver (Mac) / NVDA (Windows)

### Steps
1. **Run Lighthouse Accessibility Audit**
   - Target: 95+ score
2. **Tab through interface**
   - ✅ All interactive elements reachable
   - ✅ Focus visible
   - ✅ Logical tab order
3. **Use screen reader**
   - ✅ Heart button announces state
   - ✅ Tooltips read aloud
   - ✅ Filter chips have labels
   - ✅ Command palette navigable

### Expected
- WCAG 2.1 AA compliant
- All images have alt text
- All buttons have labels
- Color contrast > 4.5:1

---

## Error Scenarios (2 minutes)

### Test Error Handling
1. **localStorage disabled**
   - ✅ Favorites should fail gracefully
   - ✅ No infinite error loops
2. **API down**
   - ✅ Command palette shows error
   - ✅ Filters still work
3. **Network offline**
   - ✅ Cached data still works
   - ✅ Favorites work offline
4. **Invalid cluster ID**
   - ✅ Error page, not crash

---

## Visual Regression Test (3 minutes)

### Steps
1. **Take screenshots** of:
   - Cluster card with favorite (unfavorited)
   - Cluster card with favorite (favorited)
   - Enhanced tooltip open
   - Filter chips (1, 2, 3+ chips)
   - Command palette (empty search)
   - Command palette (with results)
2. **Compare** to design mockups
3. **Check** glassmorphism effects

### Visual Checklist
- ✅ Colors match design system
- ✅ Spacing consistent
- ✅ Animations smooth
- ✅ No layout shifts
- ✅ Responsive on mobile

---

## Stress Test (3 minutes)

### Scenarios
1. **100 Favorites**
   - Add many favorites via console:
   ```javascript
   localStorage.setItem('app-idea-miner-favorites', JSON.stringify(
     Array.from({length: 100}, (_, i) => ({
       id: `cluster-${i}`,
       type: 'cluster',
       timestamp: Date.now()
     }))
   ));
   ```
   - ✅ Page should still load fast
   - ✅ Favorites lookup < 1ms

2. **1000 Search Results**
   - Type single letter in command palette
   - ✅ Should render < 500ms
   - ✅ No frame drops

3. **Rapid Filter Changes**
   - Quickly toggle 10 filters
   - ✅ No race conditions
   - ✅ URL params correct

---

## Final Checklist

### Before Deployment
- [ ] All tests pass
- [ ] No console errors
- [ ] No console warnings
- [ ] Lighthouse score 95+
- [ ] Bundle size acceptable
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Git commit with message

### Deployment Steps
```bash
# 1. Commit changes
git add .
git commit -m "feat: Add Phase 8E quick win features

- Favorites/bookmarking system with localStorage
- Enhanced tooltips with rich hover cards
- Filter chips with removable badges
- Command palette (Cmd+K) with universal search
- All features fully accessible

Closes #123"

# 2. Push to branch
git push origin feature/phase-8e

# 3. Create PR
# 4. Wait for CI/CD
# 5. Deploy to staging
# 6. QA test on staging
# 7. Deploy to production
```

---

## Rollback Plan

### If Something Goes Wrong
```bash
# Revert last commit
git revert HEAD

# Or rollback to specific commit
git reset --hard <commit-hash>

# Redeploy
git push origin main --force
```

### Feature Flags (Future)
Consider adding feature flags for:
- Favorites system
- Command palette
- Enhanced tooltips
- Filter chips

This allows selective rollout and A/B testing.

---

## Support & Debugging

### Common Issues

**Issue: Favorites not persisting**
- Check: localStorage enabled in browser
- Check: No privacy mode/incognito
- Check: Browser supports localStorage API

**Issue: Cmd+K not working**
- Check: Keyboard event listeners attached
- Check: No other extension using Cmd+K
- Check: Try Ctrl+K on Windows

**Issue: Tooltips flickering**
- Check: Mouse moving too fast
- Check: z-index conflicts
- Check: Pointer-events blocking

**Issue: Filter chips not showing**
- Check: URL params being set
- Check: buildChips logic
- Check: FilterChips component imported

### Debug Commands
```javascript
// In browser console:

// Check favorites
console.log(localStorage.getItem('app-idea-miner-favorites'));

// Check recent searches
console.log(localStorage.getItem('app-idea-miner-recent-searches'));

// Clear all
localStorage.clear();

// Test command palette
const event = new KeyboardEvent('keydown', {
  key: 'k',
  metaKey: true,
  bubbles: true
});
window.dispatchEvent(event);
```

---

## Success Metrics

### Track After 1 Week
- [ ] Favorites: Average per user
- [ ] Favorites: Most favorited clusters
- [ ] Command Palette: Open rate
- [ ] Command Palette: Most searched terms
- [ ] Tooltips: Hover rate
- [ ] Filter Chips: Click-through rate

### Track After 1 Month
- [ ] User retention improvement
- [ ] Time on site increase
- [ ] Feature adoption rate
- [ ] User satisfaction scores

---

**Testing Status**: ⏳ Pending
**Estimated Time**: 30 minutes
**Priority**: High 🔴
