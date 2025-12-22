# Note Taker MVP - UI/UX Design

## User Flow

### 1. Initial Access
```
User opens web app → Google OAuth login → Grant Drive permissions
```

### 2. Session Setup (First Time / Per Session)
```
Enter Patient Name → [Optional: Select existing patient] → Ready to start
```

### 3. Transcription Session
```
[Start Button] → Recording indicator → Real-time transcript display → [Stop Button]
```

### 4. Post-Session
```
Auto-save to Drive → Success notification → Email sent confirmation
```

---

## Screen Designs

### Screen 1: Login / Welcome
```
┌─────────────────────────────────────┐
│                                     │
│    📝 Note Taker                    │
│    Secure Session Transcription     │
│                                     │
│    [Sign in with Google]            │
│                                     │
│    ✓ No recordings stored           │
│    ✓ Direct to your Google Drive    │
│    ✓ Hebrew transcription           │
│                                     │
└─────────────────────────────────────┘
```

### Screen 2: Session Setup
```
┌─────────────────────────────────────┐
│  ← Back    Note Taker               │
│                                     │
│  New Session                        │
│                                     │
│  Patient Name:                      │
│  ┌───────────────────────────────┐  │
│  │ [Enter patient name...]       │  │
│  └───────────────────────────────┘  │
│                                     │
│  📁 Save to: Clinic/Transcripts     │
│                                     │
│         [Start Session]             │
│                                     │
└─────────────────────────────────────┘
```

### Screen 3: Active Transcription
```
┌─────────────────────────────────────┐
│  ← Stop Session    Note Taker       │
│                                     │
│  🔴 Recording...                    │
│  Patient: [Patient Name]            │
│  Started: 14:30                     │
│                                     │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  │  [Real-time transcript        │  │
│  │   appears here as             │  │
│  │   speech is detected...]      │  │
│  │                               │  │
│  │  Speaker 1: שלום, איך אתה?    │  │
│  │                               │  │
│  │  Speaker 2: בסדר, תודה.       │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│         [⏹ Stop & Save]            │
│                                     │
└─────────────────────────────────────┘
```

### Screen 4: Success / Confirmation
```
┌─────────────────────────────────────┐
│                                     │
│         ✓ Session Saved!            │
│                                     │
│  Transcript saved to Google Drive   │
│  Email notification sent            │
│                                     │
│  File: PatientName_2025-12-01_14-30│
│  Location: Clinic/Transcripts       │
│                                     │
│  [View in Drive]  [New Session]    │
│                                     │
└─────────────────────────────────────┘
```

---

## Key UX Principles

### 1. **Minimal Clicks**
- One click to start (after patient name entry)
- One click to stop
- Auto-save (no manual save button)

### 2. **Visual Feedback**
- Clear recording indicator (red dot + "Recording...")
- Real-time transcript display (scrolling)
- Speaker labels (Speaker 1, Speaker 2) if available
- Success confirmation with file details

### 3. **Error Handling**
- Microphone permission denied → Clear instructions
- Network error → Retry option
- Drive save failure → Manual download option

### 4. **Privacy Indicators**
- "No recordings stored" message
- "Direct to your Google Drive" confirmation
- Clear indication that audio is not saved

---

## Technical UI Considerations

### Responsive Design
- Mobile-first (works on phone during session)
- Desktop-friendly (for review/editing)
- Touch-friendly buttons (large, clear)

### Accessibility
- High contrast text
- Large tap targets (min 44x44px)
- Screen reader support
- Keyboard navigation

### Performance
- Smooth scrolling transcript
- No lag in transcription display
- Fast page loads

---

## Color Scheme (Recommendation)

- **Primary**: Calm blue (#4A90E2) - professional, trustworthy
- **Recording**: Red (#E74C3C) - clear visual indicator
- **Success**: Green (#27AE60) - positive feedback
- **Background**: Light gray (#F5F5F5) - easy on eyes
- **Text**: Dark gray (#2C3E50) - readable

---

## Interaction States

### Start Button
- Default: Blue, "Start Session"
- Hover: Darker blue
- Active: Recording red, "Recording..."
- Disabled: Gray (if no patient name)

### Transcript Area
- Empty state: "Waiting for speech..."
- Active: Real-time text appearing
- Scroll: Auto-scroll to bottom
- Paused: "Processing..." indicator

---

## Next Steps

1. **Review this design** - Does this flow work for you?
2. **Hebrew RTL considerations** - Should UI be RTL or LTR?
3. **Patient name input** - Dropdown of recent patients or always free text?
4. **Transcript editing** - Should user be able to edit before saving?

