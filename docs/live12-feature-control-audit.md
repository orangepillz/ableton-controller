# Ableton Live 12 Feature Control Audit

Status: IN PROGRESS

## Source Manual

- URL: https://cdn-resources.ableton.com/resources/pdfs/live-manual/12/2026-04-30/live12-manual-en.pdf
- Local PDF: `data/manual/live12-manual-en-2026-04-30.pdf`
- SHA-256: `e54a087dada40726e4b78026495e69055563f7c8ab72a3d6b31aaa846c1a36ee`
- Pages extracted/read ledger: `audit/manual_pages.jsonl`
- Page count: 997
- PDF outline entries collected: 1053

## Coverage Legend

- TODO: feature/function has been identified but not yet checked against the CLI.
- COVERED: verified controllable or inspectable via `abletonctl.py` or the Live bridge.
- PARTIAL: some meaningful control exists, but Live exposes more behavior than the CLI currently covers.
- NOT POSSIBLE: best-effort investigation found no non-UI interface; reasoning is recorded.

## Feature And Function Inventory

| ID | Manual Pages | Level | Feature / Function | CLI Coverage | Evidence / Notes |
| --- | --- | ---: | --- | --- | --- |
| F0001 | 1 | 0 | Ableton Live 12 Manual | TODO | Pending verification. |
| F0002 | 1 | 1 | for Windows and Mac | TODO | Pending verification. |
| F0003 | 2-21 | 0 | Contents | TODO | Pending verification. |
| F0004 | 22 | 0 | 1. Welcome to Live | TODO | Pending verification. |
| F0005 | 22 | 1 | 1.1 The Ableton Team Says: Thank You | TODO | Pending verification. |
| F0006 | 23-32 | 0 | 2. First Steps | TODO | Pending verification. |
| F0007 | 23 | 1 | 2.1 Installation and Authorization | TODO | Pending verification. |
| F0008 | 23-29 | 1 | 2.2 Learning About Live | TODO | Pending verification. |
| F0009 | 23-27 | 2 | 2.2.1 Learn View | TODO | Pending verification. |
| F0010 | 28 | 2 | 2.2.2 Info View | TODO | Pending verification. |
| F0011 | 29 | 2 | 2.2.3 Other Learning Resources | TODO | Pending verification. |
| F0012 | 30-32 | 1 | 2.3 Live’s Settings | TODO | Pending verification. |
| F0013 | 30 | 2 | 2.3.1 Display & Input | TODO | Pending verification. |
| F0014 | 30 | 2 | 2.3.2 Theme & Colors | TODO | Pending verification. |
| F0015 | 31 | 2 | 2.3.3 Audio | TODO | Pending verification. |
| F0016 | 31 | 2 | 2.3.4 Link | TODO | Pending verification. |
| F0017 | 31 | 2 | 2.3.5 Tempo & MIDI | TODO | Pending verification. |
| F0018 | 32 | 2 | 2.3.6 File & Folder | TODO | Pending verification. |
| F0019 | 32 | 2 | 2.3.7 Library | TODO | Pending verification. |
| F0020 | 32 | 2 | 2.3.8 Plug-Ins | TODO | Pending verification. |
| F0021 | 32 | 2 | 2.3.9 Record, Warp & Launch | TODO | Pending verification. |
| F0022 | 32 | 2 | 2.3.10 Licenses & Updates | TODO | Pending verification. |
| F0023 | 33-60 | 0 | 3. Live Concepts | TODO | Pending verification. |
| F0024 | 33 | 1 | 3.1 The Control Bar | TODO | Pending verification. |
| F0025 | 34 | 1 | 3.2 The Status Bar | TODO | Pending verification. |
| F0026 | 35 | 1 | 3.3 The Browser | TODO | Pending verification. |
| F0027 | 36-37 | 1 | 3.4 Sound Similarity | TODO | Pending verification. |
| F0028 | 38 | 1 | 3.5 Live Sets | TODO | Pending verification. |
| F0029 | 38-39 | 1 | 3.6 Arrangement and Session | TODO | Pending verification. |
| F0030 | 40-42 | 1 | 3.7 Tracks | TODO | Pending verification. |
| F0031 | 43 | 1 | 3.8 Audio and MIDI | TODO | Pending verification. |
| F0032 | 44 | 1 | 3.9 Audio Clips and Samples | TODO | Pending verification. |
| F0033 | 45 | 1 | 3.10 MIDI Clips and MIDI Files | TODO | Pending verification. |
| F0034 | 46-47 | 1 | 3.11 Devices | TODO | Pending verification. |
| F0035 | 48 | 1 | 3.12 Clip and Device View | TODO | Pending verification. |
| F0036 | 49-50 | 1 | 3.13 Scale Awareness | TODO | Pending verification. |
| F0037 | 51-53 | 1 | 3.14 The Mixer | TODO | Pending verification. |
| F0038 | 54 | 1 | 3.15 Presets and Racks | TODO | Pending verification. |
| F0039 | 54 | 1 | 3.16 Routing | TODO | Pending verification. |
| F0040 | 55-56 | 1 | 3.17 Recording New Clips | TODO | Pending verification. |
| F0041 | 57 | 1 | 3.18 Automation Envelopes | TODO | Pending verification. |
| F0042 | 57 | 1 | 3.19 Clip Envelopes | TODO | Pending verification. |
| F0043 | 58 | 1 | 3.20 Undo History | TODO | Pending verification. |
| F0044 | 59 | 1 | 3.21 MIDI and Key Remote | TODO | Pending verification. |
| F0045 | 59-60 | 1 | 3.22 Saving and Exporting | TODO | Pending verification. |
| F0046 | 61-122 | 0 | 4. Working with the Browser | TODO | Pending verification. |
| F0047 | 63 | 1 | 4.1 Content Pane | TODO | Pending verification. |
| F0048 | 64-69 | 1 | 4.2 Search Bar | TODO | Pending verification. |
| F0049 | 67-69 | 2 | 4.2.1 Saving Search Results as Custom Labels | TODO | Pending verification. |
| F0050 | 70 | 1 | 4.3 Browser History | TODO | Pending verification. |
| F0051 | 71-79 | 1 | 4.4 Filters and Tags | TODO | Pending verification. |
| F0052 | 72 | 2 | 4.4.1 Filter Groups | TODO | Pending verification. |
| F0053 | 73 | 2 | 4.4.2 Tags | TODO | Pending verification. |
| F0054 | 74-77 | 2 | 4.4.3 Tag Editor | TODO | Pending verification. |
| F0055 | 78-79 | 2 | 4.4.4 Quick Tags | TODO | Pending verification. |
| F0056 | 80-81 | 1 | 4.5 Collections | TODO | Pending verification. |
| F0057 | 82-83 | 1 | 4.6 Library | TODO | Pending verification. |
| F0058 | 84-115 | 1 | 4.7 Places | TODO | Pending verification. |
| F0059 | 85-88 | 2 | 4.7.1 Downloading and Installing Packs in the Browser | TODO | Pending verification. |
| F0060 | 89 | 2 | 4.7.2 Pack Info | TODO | Pending verification. |
| F0061 | 90-103 | 2 | 4.7.3 Splice | TODO | Pending verification. |
| F0062 | 92-93 | 3 | 4.7.3.1 Logging Into Splice | TODO | Pending verification. |
| F0063 | 94-98 | 3 | 4.7.3.2 Searching for Splice Samples | TODO | Pending verification. |
| F0064 | 99-101 | 3 | 4.7.3.3 Working with Splice Samples | TODO | Pending verification. |
| F0065 | 102 | 3 | 4.7.3.4 Splice Library | TODO | Pending verification. |
| F0066 | 103 | 3 | 4.7.3.5 Splice Settings | TODO | Pending verification. |
| F0067 | 104-105 | 2 | 4.7.4 Using Ableton Cloud | TODO | Pending verification. |
| F0068 | 106-108 | 2 | 4.7.5 Transferring Files from Push 3 in Standalone Mode | TODO | Pending verification. |
| F0069 | 109-111 | 2 | 4.7.6 User Library | TODO | Pending verification. |
| F0070 | 110 | 3 | 4.7.6.1 ABL Assets | TODO | Pending verification. |
| F0071 | 110 | 3 | 4.7.6.2 Chord Banks | TODO | Pending verification. |
| F0072 | 110 | 3 | 4.7.6.3 Clips Folder | TODO | Pending verification. |
| F0073 | 111 | 3 | 4.7.6.4 Defaults Folder | TODO | Pending verification. |
| F0074 | 111 | 3 | 4.7.6.5 Grooves Folder | TODO | Pending verification. |
| F0075 | 111 | 3 | 4.7.6.6 Presets Folder | TODO | Pending verification. |
| F0076 | 111 | 3 | 4.7.6.7 Samples Folder | TODO | Pending verification. |
| F0077 | 111 | 3 | 4.7.6.8 Templates Folder | TODO | Pending verification. |
| F0078 | 112 | 3 | 4.7.6.9 Managing Files in the User Library | TODO | Pending verification. |
| F0079 | 112-113 | 2 | 4.7.7 Current Project | TODO | Pending verification. |
| F0080 | 114-115 | 2 | 4.7.8 User Folders | TODO | Pending verification. |
| F0081 | 116 | 1 | 4.8 Navigating in the Browser | TODO | Pending verification. |
| F0082 | 116-118 | 1 | 4.9 Previewing Files | TODO | Pending verification. |
| F0083 | 119-121 | 1 | 4.10 Hot-Swap Mode | TODO | Pending verification. |
| F0084 | 122 | 1 | 4.11 Adding Content from the Browser to a Live Set | TODO | Pending verification. |
| F0085 | 123-151 | 0 | 5. Managing Files and Sets | TODO | Pending verification. |
| F0086 | 123-130 | 1 | 5.1 Sample Files | TODO | Pending verification. |
| F0087 | 123 | 2 | 5.1.1 The Decoding Cache | TODO | Pending verification. |
| F0088 | 124 | 2 | 5.1.2 Analysis Files (.asd) | TODO | Pending verification. |
| F0089 | 125-130 | 2 | 5.1.3 Exporting Audio and Video | TODO | Pending verification. |
| F0090 | 125-126 | 3 | 5.1.3.1 Selection Options | TODO | Pending verification. |
| F0091 | 127 | 3 | 5.1.3.2 Rendering Options | TODO | Pending verification. |
| F0092 | 128 | 3 | 5.1.3.3 Encoding Options | TODO | Pending verification. |
| F0093 | 129 | 3 | 5.1.3.4 Video Rendering Options | TODO | Pending verification. |
| F0094 | 129-130 | 3 | 5.1.3.5 Real-Time Rendering | TODO | Pending verification. |
| F0095 | 131 | 1 | 5.2 MIDI Files | TODO | Pending verification. |
| F0096 | 131 | 2 | 5.2.1 Exporting MIDI Files | TODO | Pending verification. |
| F0097 | 132 | 1 | 5.3 Live Clips | TODO | Pending verification. |
| F0098 | 133-138 | 1 | 5.4 Live Sets | TODO | Pending verification. |
| F0099 | 133 | 2 | 5.4.1 Creating, Opening and Saving Sets | TODO | Pending verification. |
| F0100 | 133-135 | 2 | 5.4.2 Merging Sets | TODO | Pending verification. |
| F0101 | 136 | 2 | 5.4.3 Exporting Session Clips as New Sets | TODO | Pending verification. |
| F0102 | 136 | 2 | 5.4.4 Template Sets | TODO | Pending verification. |
| F0103 | 137-138 | 2 | 5.4.5 Viewing and Changing a Live Set’s File References | TODO | Pending verification. |
| F0104 | 139-143 | 1 | 5.5 Live Projects | TODO | Pending verification. |
| F0105 | 139-142 | 2 | 5.5.1 Projects and Live Sets | TODO | Pending verification. |
| F0106 | 143 | 2 | 5.5.2 Projects and Presets | TODO | Pending verification. |
| F0107 | 144 | 2 | 5.5.3 Managing Files in a Project | TODO | Pending verification. |
| F0108 | 144-146 | 1 | 5.6 Locating Missing Files | TODO | Pending verification. |
| F0109 | 145 | 2 | 5.6.1 Manual Repair | TODO | Pending verification. |
| F0110 | 145-146 | 2 | 5.6.2 Automatic Repair | TODO | Pending verification. |
| F0111 | 147-148 | 1 | 5.7 Collecting External Files | TODO | Pending verification. |
| F0112 | 148 | 2 | 5.7.1 Collect Files on Export | TODO | Pending verification. |
| F0113 | 149 | 1 | 5.8 Aggregated Locating and Collecting | TODO | Pending verification. |
| F0114 | 149 | 1 | 5.9 Finding Unused Files | TODO | Pending verification. |
| F0115 | 150 | 1 | 5.10 Packing Projects into Packs | TODO | Pending verification. |
| F0116 | 150-151 | 1 | 5.11 File Management FAQs | TODO | Pending verification. |
| F0117 | 150 | 2 | 5.11.1 How Do I Create a Project? | TODO | Pending verification. |
| F0118 | 150 | 2 | 5.11.2 How Can I Save Presets Into My Current Project? | TODO | Pending verification. |
| F0119 | 150 | 2 | 5.11.3 Can I Work On Multiple Versions of a Set? | TODO | Pending verification. |
| F0120 | 151 | 2 | 5.11.4 Where Should I Save My Live Sets? | TODO | Pending verification. |
| F0121 | 151 | 2 | 5.11.5 Can I Use My Own Folder Structure Within a Project Folder? | TODO | Pending verification. |
| F0122 | 152-173 | 0 | 6. Arrangement View | TODO | Pending verification. |
| F0123 | 152-154 | 1 | 6.1 Layout | TODO | Pending verification. |
| F0124 | 155 | 1 | 6.2 Navigation and Zooming | TODO | Pending verification. |
| F0125 | 155-156 | 1 | 6.3 Transport and Playback | TODO | Pending verification. |
| F0126 | 157-158 | 1 | 6.4 Launching the Arrangement with Locators | TODO | Pending verification. |
| F0127 | 159-160 | 1 | 6.5 Time Signature Changes | TODO | Pending verification. |
| F0128 | 161 | 1 | 6.6 The Arrangement Loop | TODO | Pending verification. |
| F0129 | 162-163 | 1 | 6.7 Moving and Resizing Clips | TODO | Pending verification. |
| F0130 | 164-165 | 1 | 6.8 Audio Clip Fades and Crossfades | TODO | Pending verification. |
| F0131 | 166 | 1 | 6.9 Selecting Clips and Time | TODO | Pending verification. |
| F0132 | 167 | 1 | 6.10 Using the Editing Grid | TODO | Pending verification. |
| F0133 | 168 | 1 | 6.11 Using the …Time Commands | TODO | Pending verification. |
| F0134 | 168 | 1 | 6.12 Splitting Clips | TODO | Pending verification. |
| F0135 | 169 | 1 | 6.13 Consolidating Clips | TODO | Pending verification. |
| F0136 | 170-171 | 1 | 6.14 Linked-Track Editing | TODO | Pending verification. |
| F0137 | 170 | 2 | 6.14.1 Linking and Unlinking Tracks | TODO | Pending verification. |
| F0138 | 171 | 2 | 6.14.2 Editing Linked Tracks | TODO | Pending verification. |
| F0139 | 172-173 | 1 | 6.15 The Mixer in Arrangement View | TODO | Pending verification. |
| F0140 | 174-186 | 0 | 7. Session View | TODO | Pending verification. |
| F0141 | 175 | 1 | 7.1 Session View Clips | TODO | Pending verification. |
| F0142 | 176-180 | 1 | 7.2 Tracks and Scenes | TODO | Pending verification. |
| F0143 | 178 | 2 | 7.2.1 Editing Scene Tempo and Time Signature Values | TODO | Pending verification. |
| F0144 | 179-180 | 2 | 7.2.2 Scene View | TODO | Pending verification. |
| F0145 | 181 | 1 | 7.3 The Track Status Fields | TODO | Pending verification. |
| F0146 | 182-183 | 1 | 7.4 Setting Up the Session View Grid | TODO | Pending verification. |
| F0147 | 183 | 2 | 7.4.1 Select on Launch | TODO | Pending verification. |
| F0148 | 183 | 2 | 7.4.2 Removing Clip Stop Buttons | TODO | Pending verification. |
| F0149 | 183 | 2 | 7.4.3 Editing Scenes | TODO | Pending verification. |
| F0150 | 184-186 | 1 | 7.5 Recording Sessions into the Arrangement | TODO | Pending verification. |
| F0151 | 187-220 | 0 | 8. Clip View | TODO | Pending verification. |
| F0152 | 188-193 | 1 | 8.1 Clip View Layout | TODO | Pending verification. |
| F0153 | 189-190 | 2 | 8.1.1 Clip Title Bar | TODO | Pending verification. |
| F0154 | 189 | 3 | 8.1.1.1 Clip Activator Toggle | TODO | Pending verification. |
| F0155 | 189 | 3 | 8.1.1.2 Clip Name | TODO | Pending verification. |
| F0156 | 190 | 3 | 8.1.1.3 Clip Color | TODO | Pending verification. |
| F0157 | 190 | 3 | 8.1.1.4 Saving Default Audio Clip Settings with the Sample | TODO | Pending verification. |
| F0158 | 191-192 | 2 | 8.1.2 Clip Panels | TODO | Pending verification. |
| F0159 | 193 | 2 | 8.1.3 Editor View Modes | TODO | Pending verification. |
| F0160 | 194-198 | 1 | 8.2 Main Clip Properties Panel | TODO | Pending verification. |
| F0161 | 195 | 2 | 8.2.1 Clip and Loop Region Settings | TODO | Pending verification. |
| F0162 | 196 | 2 | 8.2.2 Clip Time Signature | TODO | Pending verification. |
| F0163 | 197 | 2 | 8.2.3 Clip Groove | TODO | Pending verification. |
| F0164 | 198 | 2 | 8.2.4 Clip Scale | TODO | Pending verification. |
| F0165 | 199-200 | 1 | 8.3 Extended Clip Properties | TODO | Pending verification. |
| F0166 | 200 | 2 | 8.3.1 Follow Action and Launch Controls | TODO | Pending verification. |
| F0167 | 200 | 2 | 8.3.2 MIDI Clip Bank and Program Change Controls | TODO | Pending verification. |
| F0168 | 201-208 | 1 | 8.4 Audio Utilities Panel | TODO | Pending verification. |
| F0169 | 202 | 2 | 8.4.1 Warp Controls | TODO | Pending verification. |
| F0170 | 203-204 | 2 | 8.4.2 Reversing Samples | TODO | Pending verification. |
| F0171 | 205 | 2 | 8.4.3 Destructive Sample Editing | TODO | Pending verification. |
| F0172 | 205 | 2 | 8.4.4 Clip Start and End Fades | TODO | Pending verification. |
| F0173 | 206 | 2 | 8.4.5 Clip RAM Mode | TODO | Pending verification. |
| F0174 | 207 | 2 | 8.4.6 High Quality Interpolation | TODO | Pending verification. |
| F0175 | 208 | 2 | 8.4.7 Clip Gain and Pitch | TODO | Pending verification. |
| F0176 | 209-211 | 1 | 8.5 Pitch and Time Utilities Panel | TODO | Pending verification. |
| F0177 | 210 | 2 | 8.5.1 Pitch Tools | TODO | Pending verification. |
| F0178 | 211 | 2 | 8.5.2 Time Tools | TODO | Pending verification. |
| F0179 | 212 | 1 | 8.6 Transform and Generate Panels | TODO | Pending verification. |
| F0180 | 213 | 1 | 8.7 Zooming and Scrolling in the Clip View’s Editor | TODO | Pending verification. |
| F0181 | 214 | 1 | 8.8 Playing and Scrubbing Clips | TODO | Pending verification. |
| F0182 | 215-216 | 1 | 8.9 Looping Clips | TODO | Pending verification. |
| F0183 | 217 | 1 | 8.10 Clip View Sample Details | TODO | Pending verification. |
| F0184 | 218 | 1 | 8.11 Cropping Clips | TODO | Pending verification. |
| F0185 | 218 | 1 | 8.12 Replacing and Editing the Sample | TODO | Pending verification. |
| F0186 | 219 | 1 | 8.13 Editing Clip Properties for Multiple Clips | TODO | Pending verification. |
| F0187 | 219-220 | 1 | 8.14 Clip Defaults and Update Rate | TODO | Pending verification. |
| F0188 | 221-238 | 0 | 9. Audio Clips, Tempo, and Warping | TODO | Pending verification. |
| F0189 | 221-224 | 1 | 9.1 Tempo | TODO | Pending verification. |
| F0190 | 221 | 2 | 9.1.1 Setting the Tempo | TODO | Pending verification. |
| F0191 | 222 | 2 | 9.1.2 Tapping the Tempo | TODO | Pending verification. |
| F0192 | 223 | 2 | 9.1.3 Nudging the Tempo | TODO | Pending verification. |
| F0193 | 223-224 | 2 | 9.1.4 Clip Tempo Followers and Leaders | TODO | Pending verification. |
| F0194 | 225-235 | 1 | 9.2 Warping | TODO | Pending verification. |
| F0195 | 226 | 2 | 9.2.1 Warping Options in Settings | TODO | Pending verification. |
| F0196 | 227 | 2 | 9.2.2 Importing Samples | TODO | Pending verification. |
| F0197 | 227-228 | 2 | 9.2.3 Warp Markers | TODO | Pending verification. |
| F0198 | 228 | 3 | 9.2.3.1 Transients and Pseudo-Warp Markers | TODO | Pending verification. |
| F0199 | 229 | 3 | 9.2.3.2 Saving Warp Markers with a Sample File | TODO | Pending verification. |
| F0200 | 229-230 | 2 | 9.2.4 Warping Short Samples | TODO | Pending verification. |
| F0201 | 229 | 3 | 9.2.4.1 Even-Length Loops | TODO | Pending verification. |
| F0202 | 230 | 3 | 9.2.4.2 Odd-Length Loops | TODO | Pending verification. |
| F0203 | 230 | 3 | 9.2.4.3 Uneven-Length Loops | TODO | Pending verification. |
| F0204 | 231 | 3 | 9.2.4.4 Multi-Clip Warping | TODO | Pending verification. |
| F0205 | 231-234 | 2 | 9.2.5 Auto-Warping Long Samples | TODO | Pending verification. |
| F0206 | 232-234 | 3 | 9.2.5.1 Adjusting Auto-Warp Results | TODO | Pending verification. |
| F0207 | 235 | 2 | 9.2.6 Manipulating Grooves | TODO | Pending verification. |
| F0208 | 235 | 2 | 9.2.7 Quantizing Audio | TODO | Pending verification. |
| F0209 | 236-238 | 1 | 9.3 Warp Modes | TODO | Pending verification. |
| F0210 | 236 | 2 | 9.3.1 Beats Mode | TODO | Pending verification. |
| F0211 | 237 | 2 | 9.3.2 Tones Mode | TODO | Pending verification. |
| F0212 | 237 | 2 | 9.3.3 Texture Mode | TODO | Pending verification. |
| F0213 | 238 | 2 | 9.3.4 Re-Pitch Mode | TODO | Pending verification. |
| F0214 | 238 | 2 | 9.3.5 Complex and Complex Pro Mode | TODO | Pending verification. |
| F0215 | 239-279 | 0 | 10. Editing MIDI | TODO | Pending verification. |
| F0216 | 239-240 | 1 | 10.1 The MIDI Note Editor Layout | TODO | Pending verification. |
| F0217 | 241-243 | 1 | 10.2 Zooming and Navigating in the MIDI Note Editor | TODO | Pending verification. |
| F0218 | 243 | 2 | 10.2.1 Grid Snapping | TODO | Pending verification. |
| F0219 | 243 | 2 | 10.2.2 Playback Options | TODO | Pending verification. |
| F0220 | 244 | 1 | 10.3 Creating a MIDI Clip | TODO | Pending verification. |
| F0221 | 244-245 | 1 | 10.4 Adding MIDI Notes | TODO | Pending verification. |
| F0222 | 244 | 2 | 10.4.1 Draw Mode | TODO | Pending verification. |
| F0223 | 245 | 2 | 10.4.2 Previewing Notes | TODO | Pending verification. |
| F0224 | 246-270 | 1 | 10.5 Editing MIDI Notes | TODO | Pending verification. |
| F0225 | 246 | 2 | 10.5.1 Non-Destructive Editing | TODO | Pending verification. |
| F0226 | 246 | 2 | 10.5.2 Selecting Notes and Timespan | TODO | Pending verification. |
| F0227 | 247-248 | 2 | 10.5.3 Find and Select Notes | TODO | Pending verification. |
| F0228 | 249 | 2 | 10.5.4 Moving Notes | TODO | Pending verification. |
| F0229 | 249-250 | 2 | 10.5.5 Changing Note Length | TODO | Pending verification. |
| F0230 | 251 | 2 | 10.5.6 MIDI Note Stretch | TODO | Pending verification. |
| F0231 | 251 | 2 | 10.5.7 Deactivating Notes | TODO | Pending verification. |
| F0232 | 252-254 | 2 | 10.5.8 Note Operations | TODO | Pending verification. |
| F0233 | 252 | 3 | 10.5.8.1 Split | TODO | Pending verification. |
| F0234 | 253 | 3 | 10.5.8.2 Chop | TODO | Pending verification. |
| F0235 | 254 | 3 | 10.5.8.3 Join | TODO | Pending verification. |
| F0236 | 255-262 | 2 | 10.5.9 Pitch and Time Utilities | TODO | Pending verification. |
| F0237 | 255 | 3 | 10.5.9.1 Transpose | TODO | Pending verification. |
| F0238 | 255 | 3 | 10.5.9.2 Fit to Scale | TODO | Pending verification. |
| F0239 | 256 | 3 | 10.5.9.3 Invert | TODO | Pending verification. |
| F0240 | 257 | 3 | 10.5.9.4 Intervals | TODO | Pending verification. |
| F0241 | 258 | 3 | 10.5.9.5 Stretch | TODO | Pending verification. |
| F0242 | 259 | 3 | 10.5.9.6 Note Duration | TODO | Pending verification. |
| F0243 | 260 | 3 | 10.5.9.7 Humanize | TODO | Pending verification. |
| F0244 | 261 | 3 | 10.5.9.8 Reverse | TODO | Pending verification. |
| F0245 | 262 | 3 | 10.5.9.9 Legato | TODO | Pending verification. |
| F0246 | 263 | 2 | 10.5.10 MIDI Tools | TODO | Pending verification. |
| F0247 | 263 | 2 | 10.5.11 Quantizing Notes | TODO | Pending verification. |
| F0248 | 264-268 | 2 | 10.5.12 Editing Velocities | TODO | Pending verification. |
| F0249 | 268 | 3 | 10.5.12.1 Drawing Velocities | TODO | Pending verification. |
| F0250 | 268 | 3 | 10.5.12.2 Note Off Velocity | TODO | Pending verification. |
| F0251 | 269-270 | 2 | 10.5.13 Editing Probabilities | TODO | Pending verification. |
| F0252 | 270 | 3 | 10.5.13.1 Probability Groups | TODO | Pending verification. |
| F0253 | 271-273 | 1 | 10.6 Folding and Scales | TODO | Pending verification. |
| F0254 | 274-275 | 1 | 10.7 Editing MIDI Clips | TODO | Pending verification. |
| F0255 | 274 | 2 | 10.7.1 Cropping MIDI Clips | TODO | Pending verification. |
| F0256 | 275 | 2 | 10.7.2 The …Time Commands in the MIDI Note Editor | TODO | Pending verification. |
| F0257 | 275 | 2 | 10.7.3 Looping | TODO | Pending verification. |
| F0258 | 276-279 | 1 | 10.8 Multi-Clip Editing | TODO | Pending verification. |
| F0259 | 277-278 | 2 | 10.8.1 Focus Mode | TODO | Pending verification. |
| F0260 | 279 | 2 | 10.8.2 Multi-Clip Editing in the Session View | TODO | Pending verification. |
| F0261 | 279 | 2 | 10.8.3 Multi-Clip Editing in the Arrangement View | TODO | Pending verification. |
| F0262 | 280-316 | 0 | 11. MIDI Tools | TODO | Pending verification. |
| F0263 | 280-283 | 1 | 11.1 Using MIDI Tools | TODO | Pending verification. |
| F0264 | 283 | 2 | 11.1.1 Using Max for Live MIDI Tools | TODO | Pending verification. |
| F0265 | 284-307 | 1 | 11.2 Transformation Tools | TODO | Pending verification. |
| F0266 | 284 | 2 | 11.2.1 Arpeggiate | TODO | Pending verification. |
| F0267 | 285-286 | 2 | 11.2.2 Chop | TODO | Pending verification. |
| F0268 | 287-288 | 2 | 11.2.3 Connect | TODO | Pending verification. |
| F0269 | 289-290 | 2 | 11.2.4 Glissando | TODO | Pending verification. |
| F0270 | 291-292 | 2 | 11.2.5 LFO | TODO | Pending verification. |
| F0271 | 293-295 | 2 | 11.2.6 Ornament | TODO | Pending verification. |
| F0272 | 296 | 2 | 11.2.7 Quantize | TODO | Pending verification. |
| F0273 | 297-299 | 2 | 11.2.8 Recombine | TODO | Pending verification. |
| F0274 | 300-301 | 2 | 11.2.9 Span | TODO | Pending verification. |
| F0275 | 302-303 | 2 | 11.2.10 Strum | TODO | Pending verification. |
| F0276 | 304-305 | 2 | 11.2.11 Time Warp | TODO | Pending verification. |
| F0277 | 306-307 | 2 | 11.2.12 Velocity Shaper | TODO | Pending verification. |
| F0278 | 308-316 | 1 | 11.3 Generative Tools | TODO | Pending verification. |
| F0279 | 308-309 | 2 | 11.3.1 Rhythm | TODO | Pending verification. |
| F0280 | 310 | 2 | 11.3.2 Seed | TODO | Pending verification. |
| F0281 | 311-312 | 2 | 11.3.3 Shape | TODO | Pending verification. |
| F0282 | 313 | 2 | 11.3.4 Stacks | TODO | Pending verification. |
| F0283 | 314-316 | 2 | 11.3.5 Euclidean | TODO | Pending verification. |
| F0284 | 317-326 | 0 | 12. Editing MPE | TODO | Pending verification. |
| F0285 | 318 | 1 | 12.1 Viewing MPE Data | TODO | Pending verification. |
| F0286 | 319-321 | 1 | 12.2 Editing MPE Data | TODO | Pending verification. |
| F0287 | 322 | 1 | 12.3 Drawing Envelopes | TODO | Pending verification. |
| F0288 | 323 | 1 | 12.4 MPE in Live’s Devices and on Push 2 | TODO | Pending verification. |
| F0289 | 323 | 1 | 12.5 MPE in External Plug-ins | TODO | Pending verification. |
| F0290 | 323-326 | 1 | 12.6 MPE/Multi-channel Settings | TODO | Pending verification. |
| F0291 | 324-325 | 2 | 12.6.1 Accessing the MPE/Multi-channel Settings Dialog | TODO | Pending verification. |
| F0292 | 326 | 2 | 12.6.2 The MPE/Multi-Channel Settings Dialog | TODO | Pending verification. |
| F0293 | 327-331 | 0 | 13. Converting Audio to MIDI | TODO | Pending verification. |
| F0294 | 327-329 | 1 | 13.1 Slice to New MIDI Track | TODO | Pending verification. |
| F0295 | 329 | 2 | 13.1.1 Resequencing Slices | TODO | Pending verification. |
| F0296 | 329 | 2 | 13.1.2 Using Effects on Slices | TODO | Pending verification. |
| F0297 | 330 | 1 | 13.2 Convert Harmony to New MIDI Track | TODO | Pending verification. |
| F0298 | 330 | 1 | 13.3 Convert Melody to New MIDI Track | TODO | Pending verification. |
| F0299 | 331 | 1 | 13.4 Convert Drums to New MIDI Track | TODO | Pending verification. |
| F0300 | 331 | 1 | 13.5 Optimizing for Better Conversion Quality | TODO | Pending verification. |
| F0301 | 332-337 | 0 | 14. Using Grooves | TODO | Pending verification. |
| F0302 | 333-335 | 1 | 14.1 Groove Pool | TODO | Pending verification. |
| F0303 | 334 | 2 | 14.1.1 Adjusting Groove Parameters | TODO | Pending verification. |
| F0304 | 335 | 2 | 14.1.2 Committing Grooves | TODO | Pending verification. |
| F0305 | 336 | 1 | 14.2 Editing Grooves | TODO | Pending verification. |
| F0306 | 336 | 2 | 14.2.1 Extracting Grooves | TODO | Pending verification. |
| F0307 | 337 | 1 | 14.3 Groove Tips | TODO | Pending verification. |
| F0308 | 337 | 2 | 14.3.1 Grooving a Single Voice | TODO | Pending verification. |
| F0309 | 337 | 2 | 14.3.2 Non-Destructive Quantization | TODO | Pending verification. |
| F0310 | 337 | 2 | 14.3.3 Creating Texture With Randomization | TODO | Pending verification. |
| F0311 | 338-346 | 0 | 15. Using Tuning Systems | TODO | Pending verification. |
| F0312 | 340-342 | 1 | 15.1 Loading a Tuning System | TODO | Pending verification. |
| F0313 | 343 | 1 | 15.2 The Tuning Section | TODO | Pending verification. |
| F0314 | 344-345 | 1 | 15.3 MIDI Track Options for Tuning Systems | TODO | Pending verification. |
| F0315 | 344 | 2 | 15.3.1 Bypass Tuning | TODO | Pending verification. |
| F0316 | 345 | 2 | 15.3.2 MIDI Controller Layouts | TODO | Pending verification. |
| F0317 | 346 | 1 | 15.4 Learn More About Tuning Systems | TODO | Pending verification. |
| F0318 | 347-358 | 0 | 16. Launching Clips | TODO | Pending verification. |
| F0319 | 347 | 1 | 16.1 The Launch Controls | TODO | Pending verification. |
| F0320 | 348 | 1 | 16.2 Launch Modes | TODO | Pending verification. |
| F0321 | 349 | 1 | 16.3 Legato Mode | TODO | Pending verification. |
| F0322 | 350 | 1 | 16.4 Clip Launch Quantization | TODO | Pending verification. |
| F0323 | 351 | 1 | 16.5 Velocity | TODO | Pending verification. |
| F0324 | 351-352 | 1 | 16.6 Clip Offset and Nudging | TODO | Pending verification. |
| F0325 | 353-358 | 1 | 16.7 Follow Actions | TODO | Pending verification. |
| F0326 | 356 | 2 | 16.7.1 Looping Parts of a Clip | TODO | Pending verification. |
| F0327 | 357 | 2 | 16.7.2 Creating Cycles | TODO | Pending verification. |
| F0328 | 357 | 2 | 16.7.3 Temporarily Looping Clips | TODO | Pending verification. |
| F0329 | 357 | 2 | 16.7.4 Adding Variations in Sync | TODO | Pending verification. |
| F0330 | 358 | 2 | 16.7.5 Mixing up Melodies and Beats | TODO | Pending verification. |
| F0331 | 358 | 2 | 16.7.6 Creating Nonrepetitive Structures | TODO | Pending verification. |
| F0332 | 359-380 | 0 | 17. Routing and I/O | TODO | Pending verification. |
| F0333 | 361 | 1 | 17.1 Monitoring | TODO | Pending verification. |
| F0334 | 362 | 1 | 17.2 External Audio In/Out | TODO | Pending verification. |
| F0335 | 362 | 2 | 17.2.1 Mono/Stereo Conversions | TODO | Pending verification. |
| F0336 | 362-366 | 1 | 17.3 External MIDI In/Out | TODO | Pending verification. |
| F0337 | 363-364 | 2 | 17.3.1 MIDI Port Inputs and Outputs | TODO | Pending verification. |
| F0338 | 363 | 3 | 17.3.1.1 Track | TODO | Pending verification. |
| F0339 | 363-364 | 3 | 17.3.1.2 Sync | TODO | Pending verification. |
| F0340 | 365 | 3 | 17.3.1.3 Remote | TODO | Pending verification. |
| F0341 | 365 | 2 | 17.3.2 Playing MIDI With the Computer Keyboard | TODO | Pending verification. |
| F0342 | 366 | 2 | 17.3.3 Connecting External Synthesizers | TODO | Pending verification. |
| F0343 | 366 | 2 | 17.3.4 MIDI In/Out Indicators | TODO | Pending verification. |
| F0344 | 367 | 1 | 17.4 Resampling | TODO | Pending verification. |
| F0345 | 367-380 | 1 | 17.5 Internal Routings | TODO | Pending verification. |
| F0346 | 368-369 | 2 | 17.5.1 Internal Routing Points | TODO | Pending verification. |
| F0347 | 370 | 3 | 17.5.1.1 Routing Points in Racks | TODO | Pending verification. |
| F0348 | 370-380 | 2 | 17.5.2 Making Use of Internal Routing | TODO | Pending verification. |
| F0349 | 371 | 3 | 17.5.2.1 Post-Effects Recording | TODO | Pending verification. |
| F0350 | 372 | 3 | 17.5.2.2 Recording MIDI as Audio | TODO | Pending verification. |
| F0351 | 373 | 3 | 17.5.2.3 Creating Submixes | TODO | Pending verification. |
| F0352 | 374-375 | 3 | 17.5.2.4 Several MIDI Tracks Playing the Same Instrument | TODO | Pending verification. |
| F0353 | 376 | 3 | 17.5.2.5 Tapping Individual Outs From an Instrument | TODO | Pending verification. |
| F0354 | 377-378 | 3 | 17.5.2.6 Using Multi-Timbral Plug-In Instruments | TODO | Pending verification. |
| F0355 | 379 | 3 | 17.5.2.7 Feeding Sidechain Inputs | TODO | Pending verification. |
| F0356 | 379-380 | 3 | 17.5.2.8 Layering Instruments | TODO | Pending verification. |
| F0357 | 381-396 | 0 | 18. Mixing | TODO | Pending verification. |
| F0358 | 381-384 | 1 | 18.1 The Live Mixer | TODO | Pending verification. |
| F0359 | 384 | 2 | 18.1.1 Additional Mixer Features | TODO | Pending verification. |
| F0360 | 385 | 1 | 18.2 Audio and MIDI Tracks | TODO | Pending verification. |
| F0361 | 386-387 | 1 | 18.3 Group Tracks | TODO | Pending verification. |
| F0362 | 388-389 | 1 | 18.4 Return Tracks and the Main track | TODO | Pending verification. |
| F0363 | 390-392 | 1 | 18.5 Using Live’s Crossfader | TODO | Pending verification. |
| F0364 | 393-394 | 1 | 18.6 Soloing and Cueing | TODO | Pending verification. |
| F0365 | 395 | 1 | 18.7 Track Delays | TODO | Pending verification. |
| F0366 | 395 | 1 | 18.8 Keep Monitoring Latency in Recording Track Toggles | TODO | Pending verification. |
| F0367 | 396 | 1 | 18.9 Performance Impact Track Indicators | TODO | Pending verification. |
| F0368 | 397-409 | 0 | 19. Recording New Clips | TODO | Pending verification. |
| F0369 | 397 | 1 | 19.1 Choosing an Input | TODO | Pending verification. |
| F0370 | 398 | 1 | 19.2 Arming (Record-Enabling) Tracks | TODO | Pending verification. |
| F0371 | 398-401 | 1 | 19.3 Recording | TODO | Pending verification. |
| F0372 | 399 | 2 | 19.3.1 Recording Into the Arrangement | TODO | Pending verification. |
| F0373 | 399-400 | 2 | 19.3.2 Recording Into Session Slots | TODO | Pending verification. |
| F0374 | 401 | 2 | 19.3.3 Overdub Recording MIDI Patterns | TODO | Pending verification. |
| F0375 | 401 | 2 | 19.3.4 MIDI Step Recording | TODO | Pending verification. |
| F0376 | 402-403 | 1 | 19.4 Recording in Sync | TODO | Pending verification. |
| F0377 | 404 | 2 | 19.4.1 Metronome Settings | TODO | Pending verification. |
| F0378 | 404 | 1 | 19.5 Recording Quantized MIDI Notes | TODO | Pending verification. |
| F0379 | 405 | 1 | 19.6 Recording with Count-in | TODO | Pending verification. |
| F0380 | 405 | 1 | 19.7 Setting up File Types | TODO | Pending verification. |
| F0381 | 405 | 1 | 19.8 Where are the Recorded Samples? | TODO | Pending verification. |
| F0382 | 406 | 1 | 19.9 Using Remote Control for Recording | TODO | Pending verification. |
| F0383 | 407-409 | 1 | 19.10 Capturing MIDI | TODO | Pending verification. |
| F0384 | 408 | 2 | 19.10.1 Starting a New Live Set | TODO | Pending verification. |
| F0385 | 409 | 2 | 19.10.2 Adding Material to an Existing Live Set | TODO | Pending verification. |
| F0386 | 410-415 | 0 | 20. Bounce to Audio | TODO | Pending verification. |
| F0387 | 410-411 | 1 | 20.1 Bouncing Individual Tracks | TODO | Pending verification. |
| F0388 | 412-413 | 1 | 20.2 Bouncing Group Tracks | TODO | Pending verification. |
| F0389 | 414-415 | 1 | 20.3 Pasting Bounced Audio | TODO | Pending verification. |
| F0390 | 416-421 | 0 | 21. Comping | TODO | Pending verification. |
| F0391 | 416-417 | 1 | 21.1 Take Lanes | TODO | Pending verification. |
| F0392 | 418 | 1 | 21.2 Inserting and Managing Take Lanes | TODO | Pending verification. |
| F0393 | 418 | 1 | 21.3 Recording Takes | TODO | Pending verification. |
| F0394 | 419 | 1 | 21.4 Inserting Samples | TODO | Pending verification. |
| F0395 | 419 | 1 | 21.5 Auditioning Take Lanes | TODO | Pending verification. |
| F0396 | 420 | 1 | 21.6 Creating a Comp | TODO | Pending verification. |
| F0397 | 421 | 1 | 21.7 Source Highlights | TODO | Pending verification. |
| F0398 | 422-429 | 0 | 22. Stem Separation | TODO | Pending verification. |
| F0399 | 422 | 1 | 22.1 How Stem Separation Works in Live | TODO | Pending verification. |
| F0400 | 422-429 | 1 | 22.2 Separating Audio Files and Clips | TODO | Pending verification. |
| F0401 | 428-429 | 2 | 22.2.1 Separation Speed vs. Quality | TODO | Pending verification. |
| F0402 | 430-459 | 0 | 23. Working with Instruments and Effects | TODO | Pending verification. |
| F0403 | 430-431 | 1 | 23.1 Device View | TODO | Pending verification. |
| F0404 | 432-446 | 1 | 23.2 Using Devices | TODO | Pending verification. |
| F0405 | 435-438 | 2 | 23.2.1 Device Title Bar | TODO | Pending verification. |
| F0406 | 439-442 | 2 | 23.2.2 Device A/B Comparison | TODO | Pending verification. |
| F0407 | 443 | 2 | 23.2.3 Live Device Presets | TODO | Pending verification. |
| F0408 | 444 | 2 | 23.2.4 Saving Presets | TODO | Pending verification. |
| F0409 | 444-446 | 2 | 23.2.5 Default Presets | TODO | Pending verification. |
| F0410 | 447-452 | 1 | 23.3 Using Plug-Ins | TODO | Pending verification. |
| F0411 | 448-451 | 2 | 23.3.1 Plug-Ins in the Device View | TODO | Pending verification. |
| F0412 | 450 | 3 | 23.3.1.1 Showing Plug-In Panels in Separate Windows | TODO | Pending verification. |
| F0413 | 451 | 3 | 23.3.1.2 Plug-In Configure Mode | TODO | Pending verification. |
| F0414 | 452 | 2 | 23.3.2 Sidechain Parameters | TODO | Pending verification. |
| F0415 | 453-456 | 1 | 23.4 VST Plug-Ins | TODO | Pending verification. |
| F0416 | 453-455 | 2 | 23.4.1 The VST Plug-In Folder | TODO | Pending verification. |
| F0417 | 456 | 2 | 23.4.2 VST Presets and Banks | TODO | Pending verification. |
| F0418 | 457 | 1 | 23.5 Audio Units Plug-Ins | TODO | Pending verification. |
| F0419 | 458-459 | 1 | 23.6 Device Delay Compensation | TODO | Pending verification. |
| F0420 | 460-479 | 0 | 24. Instrument, Drum and Effect Racks | TODO | Pending verification. |
| F0421 | 460-461 | 1 | 24.1 An Overview of Racks | TODO | Pending verification. |
| F0422 | 460 | 2 | 24.1.1 Signal Flow and Parallel Device Chains | TODO | Pending verification. |
| F0423 | 461 | 2 | 24.1.2 Macro Controls | TODO | Pending verification. |
| F0424 | 462 | 1 | 24.2 Creating Racks | TODO | Pending verification. |
| F0425 | 463 | 1 | 24.3 Looking at Racks | TODO | Pending verification. |
| F0426 | 464-465 | 1 | 24.4 Chain List | TODO | Pending verification. |
| F0427 | 465 | 2 | 24.4.1 Auto Select | TODO | Pending verification. |
| F0428 | 466-469 | 1 | 24.5 Zones | TODO | Pending verification. |
| F0429 | 466 | 2 | 24.5.1 Signal Flow through Zones | TODO | Pending verification. |
| F0430 | 467 | 2 | 24.5.2 Key Zones | TODO | Pending verification. |
| F0431 | 467 | 2 | 24.5.3 Velocity Zones | TODO | Pending verification. |
| F0432 | 468-469 | 2 | 24.5.4 Chain Select Zones | TODO | Pending verification. |
| F0433 | 469 | 3 | 24.5.4.1 Making Preset Banks Using Chain Select | TODO | Pending verification. |
| F0434 | 469 | 3 | 24.5.4.2 Crossfading Preset Banks Using Fade Ranges | TODO | Pending verification. |
| F0435 | 470-472 | 1 | 24.6 Drum Racks | TODO | Pending verification. |
| F0436 | 471-472 | 2 | 24.6.1 Pad View | TODO | Pending verification. |
| F0437 | 473-476 | 1 | 24.7 Using the Macro Controls | TODO | Pending verification. |
| F0438 | 473 | 2 | 24.7.1 Map Mode | TODO | Pending verification. |
| F0439 | 474-475 | 2 | 24.7.2 Randomizing Macro Controls | TODO | Pending verification. |
| F0440 | 476 | 2 | 24.7.3 Macro Control Variations | TODO | Pending verification. |
| F0441 | 477-479 | 1 | 24.8 Mixing With Racks | TODO | Pending verification. |
| F0442 | 478-479 | 2 | 24.8.1 Extracting Chains | TODO | Pending verification. |
| F0443 | 480-492 | 0 | 25. Automation and Editing Envelopes | TODO | Pending verification. |
| F0444 | 480 | 1 | 25.1 Recording Automation in Arrangement View | TODO | Pending verification. |
| F0445 | 481-482 | 1 | 25.2 Recording Automation in Session View | TODO | Pending verification. |
| F0446 | 483 | 2 | 25.2.1 Session Automation Recording Modes | TODO | Pending verification. |
| F0447 | 483 | 1 | 25.3 Deleting Automation | TODO | Pending verification. |
| F0448 | 483 | 1 | 25.4 Overriding Automation | TODO | Pending verification. |
| F0449 | 484-492 | 1 | 25.5 Drawing and Editing Automation | TODO | Pending verification. |
| F0450 | 485 | 2 | 25.5.1 Drawing Envelopes | TODO | Pending verification. |
| F0451 | 486-487 | 2 | 25.5.2 Editing Breakpoints | TODO | Pending verification. |
| F0452 | 488 | 2 | 25.5.3 Stretching and Skewing Envelopes | TODO | Pending verification. |
| F0453 | 489 | 2 | 25.5.4 Simplifying Envelopes | TODO | Pending verification. |
| F0454 | 490 | 2 | 25.5.5 Inserting Automation Shapes | TODO | Pending verification. |
| F0455 | 491 | 2 | 25.5.6 Locking Envelopes | TODO | Pending verification. |
| F0456 | 491 | 2 | 25.5.7 Edit Menu Commands | TODO | Pending verification. |
| F0457 | 491-492 | 2 | 25.5.8 Editing the Tempo Automation | TODO | Pending verification. |
| F0458 | 493-504 | 0 | 26. Clip Envelopes | TODO | Pending verification. |
| F0459 | 493 | 1 | 26.1 The Clip Envelope Editor | TODO | Pending verification. |
| F0460 | 494-496 | 1 | 26.2 Audio Clip Envelopes | TODO | Pending verification. |
| F0461 | 494 | 2 | 26.2.1 Clip Envelopes are Non-Destructive | TODO | Pending verification. |
| F0462 | 494 | 2 | 26.2.2 Changing Pitch and Tuning per Note | TODO | Pending verification. |
| F0463 | 495 | 2 | 26.2.3 Muting or Attenuating Notes in a Sample | TODO | Pending verification. |
| F0464 | 496 | 2 | 26.2.4 Scrambling Beats | TODO | Pending verification. |
| F0465 | 497 | 2 | 26.2.5 Using Clips as Templates | TODO | Pending verification. |
| F0466 | 497-500 | 1 | 26.3 Mixer and Device Clip Envelopes | TODO | Pending verification. |
| F0467 | 499 | 2 | 26.3.1 Modulating Mixer Volumes and Sends | TODO | Pending verification. |
| F0468 | 500 | 2 | 26.3.2 Modulating Pan | TODO | Pending verification. |
| F0469 | 500 | 2 | 26.3.3 Modulating Device Controls | TODO | Pending verification. |
| F0470 | 501 | 1 | 26.4 MIDI Controller Clip Envelopes | TODO | Pending verification. |
| F0471 | 501-504 | 1 | 26.5 Unlinking Clip Envelopes From Clips | TODO | Pending verification. |
| F0472 | 502 | 2 | 26.5.1 Programming a Fade-Out for a Live Set | TODO | Pending verification. |
| F0473 | 502 | 2 | 26.5.2 Creating Long Loops from Short Loops | TODO | Pending verification. |
| F0474 | 503 | 2 | 26.5.3 Imposing Rhythm Patterns onto Samples | TODO | Pending verification. |
| F0475 | 503 | 2 | 26.5.4 Clip Envelopes as LFOs | TODO | Pending verification. |
| F0476 | 503-504 | 2 | 26.5.5 Warping Linked Envelopes | TODO | Pending verification. |
| F0477 | 505-510 | 0 | 27. Working with Video | TODO | Pending verification. |
| F0478 | 505 | 1 | 27.1 Importing Video | TODO | Pending verification. |
| F0479 | 505-507 | 1 | 27.2 The Appearance of Video in Live | TODO | Pending verification. |
| F0480 | 505 | 2 | 27.2.1 Video Clips in the Arrangement View | TODO | Pending verification. |
| F0481 | 506 | 2 | 27.2.2 The Video Window | TODO | Pending verification. |
| F0482 | 507 | 3 | 27.2.2.1 Movies with Partial Tracks | TODO | Pending verification. |
| F0483 | 507 | 2 | 27.2.3 Clip View | TODO | Pending verification. |
| F0484 | 507 | 3 | 27.2.3.1 Warp Markers | TODO | Pending verification. |
| F0485 | 508 | 1 | 27.3 Matching Sound to Video | TODO | Pending verification. |
| F0486 | 508-510 | 1 | 27.4 Video Trimming Tricks | TODO | Pending verification. |
| F0487 | 511-649 | 0 | 28. Live Audio Effect Reference | TODO | Pending verification. |
| F0488 | 511-512 | 1 | 28.1 Amp | TODO | Pending verification. |
| F0489 | 512 | 2 | 28.1.1 Amp Tips | TODO | Pending verification. |
| F0490 | 512 | 3 | 28.1.1.1 Amps and Cabinets | TODO | Pending verification. |
| F0491 | 513 | 3 | 28.1.1.2 Electricity | TODO | Pending verification. |
| F0492 | 513 | 3 | 28.1.1.3 More than Guitars | TODO | Pending verification. |
| F0493 | 513-520 | 1 | 28.2 Auto Filter | TODO | Pending verification. |
| F0494 | 514 | 2 | 28.2.1 Filter Types | TODO | Pending verification. |
| F0495 | 515 | 2 | 28.2.2 Filter Display | TODO | Pending verification. |
| F0496 | 516 | 2 | 28.2.3 LFO Controls | TODO | Pending verification. |
| F0497 | 517 | 2 | 28.2.4 Envelope Follower Controls | TODO | Pending verification. |
| F0498 | 518 | 2 | 28.2.5 Filter Drive and Circuits | TODO | Pending verification. |
| F0499 | 519 | 2 | 28.2.6 Global Controls | TODO | Pending verification. |
| F0500 | 519-520 | 2 | 28.2.7 Sidechain Parameters | TODO | Pending verification. |
| F0501 | 521 | 3 | 28.2.7.1 Mono Sidechain | TODO | Pending verification. |
| F0502 | 521-524 | 1 | 28.3 Auto Pan-Tremolo | TODO | Pending verification. |
| F0503 | 525-532 | 1 | 28.4 Auto Shift | TODO | Pending verification. |
| F0504 | 526-527 | 2 | 28.4.1 Input Section | TODO | Pending verification. |
| F0505 | 527 | 3 | 28.4.1.1 MIDI Input | TODO | Pending verification. |
| F0506 | 528 | 2 | 28.4.2 Quantizer Tab | TODO | Pending verification. |
| F0507 | 529 | 2 | 28.4.3 MIDI Tab | TODO | Pending verification. |
| F0508 | 530 | 2 | 28.4.4 LFO Tab | TODO | Pending verification. |
| F0509 | 531 | 2 | 28.4.5 Pitch Section | TODO | Pending verification. |
| F0510 | 532 | 2 | 28.4.6 Vibrato Section | TODO | Pending verification. |
| F0511 | 533-534 | 1 | 28.5 Beat Repeat | TODO | Pending verification. |
| F0512 | 535-536 | 1 | 28.6 Cabinet | TODO | Pending verification. |
| F0513 | 536 | 2 | 28.6.1 Cabinet Tips | TODO | Pending verification. |
| F0514 | 536 | 3 | 28.6.1.1 Amps and Cabinets | TODO | Pending verification. |
| F0515 | 537 | 3 | 28.6.1.2 Multiple mics | TODO | Pending verification. |
| F0516 | 537-538 | 1 | 28.7 Channel EQ | TODO | Pending verification. |
| F0517 | 538 | 2 | 28.7.1 Channel EQ Tips | TODO | Pending verification. |
| F0518 | 539-542 | 1 | 28.8 Chorus-Ensemble | TODO | Pending verification. |
| F0519 | 542 | 2 | 28.8.1 Chorus-Ensemble Tips | TODO | Pending verification. |
| F0520 | 543-547 | 1 | 28.9 Compressor | TODO | Pending verification. |
| F0521 | 546 | 2 | 28.9.1 Sidechain Parameters | TODO | Pending verification. |
| F0522 | 547 | 2 | 28.9.2 Compressor Tips | TODO | Pending verification. |
| F0523 | 547 | 3 | 28.9.2.1 Mixing a Voiceover | TODO | Pending verification. |
| F0524 | 547 | 3 | 28.9.2.2 Sidechaining in Dance Music | TODO | Pending verification. |
| F0525 | 548-553 | 1 | 28.10 Corpus | TODO | Pending verification. |
| F0526 | 549-550 | 2 | 28.10.1 Resonator Parameters | TODO | Pending verification. |
| F0527 | 551 | 2 | 28.10.2 LFO Section | TODO | Pending verification. |
| F0528 | 552 | 2 | 28.10.3 Filter Section | TODO | Pending verification. |
| F0529 | 553 | 2 | 28.10.4 Global Parameters | TODO | Pending verification. |
| F0530 | 553 | 2 | 28.10.5 Sidechain Parameters | TODO | Pending verification. |
| F0531 | 554-557 | 1 | 28.11 Delay | TODO | Pending verification. |
| F0532 | 557 | 2 | 28.11.1 Context Menu Options for Delay | TODO | Pending verification. |
| F0533 | 557 | 2 | 28.11.2 Delay Tips | TODO | Pending verification. |
| F0534 | 557 | 3 | 28.11.2.1 Glitch Effect | TODO | Pending verification. |
| F0535 | 557 | 3 | 28.11.2.2 Chorus Effect | TODO | Pending verification. |
| F0536 | 558-559 | 1 | 28.12 Drum Buss | TODO | Pending verification. |
| F0537 | 559 | 2 | 28.12.0.1 Mid-High Frequency Shaping | TODO | Pending verification. |
| F0538 | 559 | 2 | 28.12.0.2 Low-End Enhancement | TODO | Pending verification. |
| F0539 | 559 | 2 | 28.12.0.3 Output | TODO | Pending verification. |
| F0540 | 560 | 1 | 28.13 Dynamic Tube | TODO | Pending verification. |
| F0541 | 561-564 | 1 | 28.14 Echo | TODO | Pending verification. |
| F0542 | 562 | 2 | 28.14.1 Echo Tab | TODO | Pending verification. |
| F0543 | 563 | 2 | 28.14.2 Modulation Tab | TODO | Pending verification. |
| F0544 | 563 | 2 | 28.14.3 Character Tab | TODO | Pending verification. |
| F0545 | 564 | 2 | 28.14.4 Global Controls | TODO | Pending verification. |
| F0546 | 565-566 | 1 | 28.15 EQ Eight | TODO | Pending verification. |
| F0547 | 567 | 2 | 28.15.0.1 Context Menu Options for EQ Eight | TODO | Pending verification. |
| F0548 | 567 | 1 | 28.16 EQ Three | TODO | Pending verification. |
| F0549 | 568 | 1 | 28.17 Erosion | TODO | Pending verification. |
| F0550 | 569-570 | 1 | 28.18 External Audio Effect | TODO | Pending verification. |
| F0551 | 571 | 1 | 28.19 Filter Delay | TODO | Pending verification. |
| F0552 | 572-573 | 1 | 28.20 Gate | TODO | Pending verification. |
| F0553 | 574-576 | 1 | 28.21 Glue Compressor | TODO | Pending verification. |
| F0554 | 575-576 | 2 | 28.21.1 Sidechain Parameters | TODO | Pending verification. |
| F0555 | 576 | 3 | 28.21.1.1 Context Menu Options for Glue Compressor | TODO | Pending verification. |
| F0556 | 577 | 1 | 28.22 Grain Delay | TODO | Pending verification. |
| F0557 | 578-584 | 1 | 28.23 Hybrid Reverb | TODO | Pending verification. |
| F0558 | 579 | 2 | 28.23.1 Signal Flow | TODO | Pending verification. |
| F0559 | 579 | 2 | 28.23.2 Input Section | TODO | Pending verification. |
| F0560 | 580 | 2 | 28.23.3 Convolution Reverb Engine | TODO | Pending verification. |
| F0561 | 581-583 | 2 | 28.23.4 Algorithmic Reverb Engine | TODO | Pending verification. |
| F0562 | 581 | 3 | 28.23.4.1 Dark Hall | TODO | Pending verification. |
| F0563 | 582 | 3 | 28.23.4.2 Quartz | TODO | Pending verification. |
| F0564 | 582 | 3 | 28.23.4.3 Shimmer | TODO | Pending verification. |
| F0565 | 583 | 3 | 28.23.4.4 Tides | TODO | Pending verification. |
| F0566 | 583 | 3 | 28.23.4.5 Prism | TODO | Pending verification. |
| F0567 | 584 | 2 | 28.23.5 EQ Section | TODO | Pending verification. |
| F0568 | 584 | 2 | 28.23.6 Output Section | TODO | Pending verification. |
| F0569 | 585-586 | 1 | 28.24 Limiter | TODO | Pending verification. |
| F0570 | 587-590 | 1 | 28.25 Looper | TODO | Pending verification. |
| F0571 | 590 | 2 | 28.25.1 Feedback Routing | TODO | Pending verification. |
| F0572 | 591-595 | 1 | 28.26 Multiband Dynamics | TODO | Pending verification. |
| F0573 | 591 | 2 | 28.26.1 Dynamics Processing Theory | TODO | Pending verification. |
| F0574 | 592-593 | 2 | 28.26.2 Interface and Controls | TODO | Pending verification. |
| F0575 | 594 | 2 | 28.26.3 Sidechain Parameters | TODO | Pending verification. |
| F0576 | 595 | 2 | 28.26.4 Multiband Dynamics Tips | TODO | Pending verification. |
| F0577 | 595 | 3 | 28.26.4.1 Basic Multiband Compression | TODO | Pending verification. |
| F0578 | 595 | 3 | 28.26.4.2 De-essing | TODO | Pending verification. |
| F0579 | 595 | 3 | 28.26.4.3 Uncompression | TODO | Pending verification. |
| F0580 | 596 | 1 | 28.27 Overdrive | TODO | Pending verification. |
| F0581 | 597-599 | 1 | 28.28 Pedal | TODO | Pending verification. |
| F0582 | 598-599 | 2 | 28.28.1 Pedal Tips | TODO | Pending verification. |
| F0583 | 598 | 3 | 28.28.1.1 Positioning Pedal in the Device Chain | TODO | Pending verification. |
| F0584 | 598 | 3 | 28.28.1.2 Techno Kick | TODO | Pending verification. |
| F0585 | 599 | 3 | 28.28.1.3 Drum Group Fizzle | TODO | Pending verification. |
| F0586 | 599 | 3 | 28.28.1.4 Broken Speaker | TODO | Pending verification. |
| F0587 | 599 | 3 | 28.28.1.5 Sub Warmer | TODO | Pending verification. |
| F0588 | 600-602 | 1 | 28.29 Phaser-Flanger | TODO | Pending verification. |
| F0589 | 603-604 | 1 | 28.30 Redux | TODO | Pending verification. |
| F0590 | 604 | 2 | 28.30.1 Downsampling | TODO | Pending verification. |
| F0591 | 604 | 2 | 28.30.2 Bit Reduction | TODO | Pending verification. |
| F0592 | 605 | 1 | 28.31 Resonators | TODO | Pending verification. |
| F0593 | 606-609 | 1 | 28.32 Reverb | TODO | Pending verification. |
| F0594 | 607 | 2 | 28.32.1 Input Filter | TODO | Pending verification. |
| F0595 | 607 | 2 | 28.32.2 Early Reflections | TODO | Pending verification. |
| F0596 | 608 | 2 | 28.32.3 Diffusion Network | TODO | Pending verification. |
| F0597 | 608 | 2 | 28.32.4 Chorus | TODO | Pending verification. |
| F0598 | 609 | 2 | 28.32.5 Global Settings | TODO | Pending verification. |
| F0599 | 610 | 2 | 28.32.6 Output | TODO | Pending verification. |
| F0600 | 610-618 | 1 | 28.33 Roar | TODO | Pending verification. |
| F0601 | 611 | 2 | 28.33.1 Input Section | TODO | Pending verification. |
| F0602 | 612-613 | 2 | 28.33.2 Gain Stage Section | TODO | Pending verification. |
| F0603 | 614-615 | 2 | 28.33.3 Modulation Section | TODO | Pending verification. |
| F0604 | 616 | 2 | 28.33.4 Feedback Section | TODO | Pending verification. |
| F0605 | 617 | 2 | 28.33.5 Global Section | TODO | Pending verification. |
| F0606 | 618 | 2 | 28.33.6 Sidechain Parameters | TODO | Pending verification. |
| F0607 | 619-621 | 1 | 28.34 Saturator | TODO | Pending verification. |
| F0608 | 621 | 2 | 28.34.0.1 Saturator’s Waveshaper Controls | TODO | Pending verification. |
| F0609 | 622 | 2 | 28.34.0.2 Context Menu Options for Saturator | TODO | Pending verification. |
| F0610 | 622-626 | 1 | 28.35 Shifter | TODO | Pending verification. |
| F0611 | 623 | 2 | 28.35.1 Tuning and Delay Section | TODO | Pending verification. |
| F0612 | 624 | 2 | 28.35.2 LFO Section | TODO | Pending verification. |
| F0613 | 625 | 2 | 28.35.3 Envelope Follower Section | TODO | Pending verification. |
| F0614 | 625 | 2 | 28.35.4 Shifter Mode Section | TODO | Pending verification. |
| F0615 | 626 | 2 | 28.35.5 Sidechain Parameters | TODO | Pending verification. |
| F0616 | 627 | 2 | 28.35.6 Shifter Tips | TODO | Pending verification. |
| F0617 | 627 | 3 | 28.35.6.1 Pitch-shifted Drum Layers | TODO | Pending verification. |
| F0618 | 627 | 3 | 28.35.6.2 Phasing Effects | TODO | Pending verification. |
| F0619 | 627 | 3 | 28.35.6.3 Tremolo Effects | TODO | Pending verification. |
| F0620 | 627-631 | 1 | 28.36 Spectral Resonator | TODO | Pending verification. |
| F0621 | 628 | 2 | 28.36.1 Pitch Mode Section | TODO | Pending verification. |
| F0622 | 629 | 2 | 28.36.2 Frequency Section | TODO | Pending verification. |
| F0623 | 630 | 2 | 28.36.3 Modulation Section | TODO | Pending verification. |
| F0624 | 630 | 2 | 28.36.4 Spectrogram | TODO | Pending verification. |
| F0625 | 631 | 2 | 28.36.5 Global Parameters | TODO | Pending verification. |
| F0626 | 632 | 2 | 28.36.6 Spectral Resonator Tips | TODO | Pending verification. |
| F0627 | 632-635 | 1 | 28.37 Spectral Time | TODO | Pending verification. |
| F0628 | 633 | 2 | 28.37.1 Freezer Section | TODO | Pending verification. |
| F0629 | 634 | 2 | 28.37.2 Delay Section | TODO | Pending verification. |
| F0630 | 635 | 2 | 28.37.3 Resolution Section | TODO | Pending verification. |
| F0631 | 635 | 2 | 28.37.4 Global Controls | TODO | Pending verification. |
| F0632 | 636 | 1 | 28.38 Spectrum | TODO | Pending verification. |
| F0633 | 637-642 | 1 | 28.39 Tuner | TODO | Pending verification. |
| F0634 | 638 | 2 | 28.39.1 View Switches | TODO | Pending verification. |
| F0635 | 638-639 | 2 | 28.39.2 Classic View | TODO | Pending verification. |
| F0636 | 640 | 2 | 28.39.3 Histogram View | TODO | Pending verification. |
| F0637 | 641 | 2 | 28.39.4 Note Spellings | TODO | Pending verification. |
| F0638 | 642 | 2 | 28.39.5 Reference Slider | TODO | Pending verification. |
| F0639 | 643-644 | 1 | 28.40 Utility | TODO | Pending verification. |
| F0640 | 645 | 1 | 28.41 Vinyl Distortion | TODO | Pending verification. |
| F0641 | 646-649 | 1 | 28.42 Vocoder | TODO | Pending verification. |
| F0642 | 648-649 | 2 | 28.42.1 Vocoder Tips | TODO | Pending verification. |
| F0643 | 648 | 3 | 28.42.1.1 Singing Synthesizer | TODO | Pending verification. |
| F0644 | 648-649 | 3 | 28.42.1.2 Formant Shifter | TODO | Pending verification. |
| F0645 | 650-662 | 0 | 29. Live MIDI Effect Reference | TODO | Pending verification. |
| F0646 | 650-652 | 1 | 29.1 Arpeggiator | TODO | Pending verification. |
| F0647 | 653 | 1 | 29.2 CC Control | TODO | Pending verification. |
| F0648 | 654-655 | 1 | 29.3 Chord | TODO | Pending verification. |
| F0649 | 656 | 1 | 29.4 Note Length | TODO | Pending verification. |
| F0650 | 657 | 1 | 29.5 Pitch | TODO | Pending verification. |
| F0651 | 658-659 | 1 | 29.6 Random | TODO | Pending verification. |
| F0652 | 660 | 1 | 29.7 Scale | TODO | Pending verification. |
| F0653 | 661-662 | 1 | 29.8 Velocity | TODO | Pending verification. |
| F0654 | 663-782 | 0 | 30. Live Instrument Reference | TODO | Pending verification. |
| F0655 | 663-671 | 1 | 30.1 Analog | TODO | Pending verification. |
| F0656 | 663 | 2 | 30.1.1 Architecture and Interface | TODO | Pending verification. |
| F0657 | 664-665 | 2 | 30.1.2 Oscillators | TODO | Pending verification. |
| F0658 | 666 | 2 | 30.1.3 Noise Generator | TODO | Pending verification. |
| F0659 | 666 | 2 | 30.1.4 Filters | TODO | Pending verification. |
| F0660 | 667 | 2 | 30.1.5 Amplifiers | TODO | Pending verification. |
| F0661 | 668 | 2 | 30.1.6 Envelopes | TODO | Pending verification. |
| F0662 | 669 | 2 | 30.1.7 LFOs | TODO | Pending verification. |
| F0663 | 670 | 2 | 30.1.8 Global Parameters | TODO | Pending verification. |
| F0664 | 671 | 2 | 30.1.9 MPE Sources | TODO | Pending verification. |
| F0665 | 672-680 | 1 | 30.2 Collision | TODO | Pending verification. |
| F0666 | 672 | 2 | 30.2.1 Architecture and Interface | TODO | Pending verification. |
| F0667 | 673 | 2 | 30.2.2 Mallet Section | TODO | Pending verification. |
| F0668 | 674 | 2 | 30.2.3 Noise Section | TODO | Pending verification. |
| F0669 | 675-677 | 2 | 30.2.4 Resonator Tabs | TODO | Pending verification. |
| F0670 | 677 | 3 | 30.2.4.1 Tuning Section | TODO | Pending verification. |
| F0671 | 677 | 3 | 30.2.4.2 Mixer Section | TODO | Pending verification. |
| F0672 | 678 | 2 | 30.2.5 LFO Tab | TODO | Pending verification. |
| F0673 | 679 | 2 | 30.2.6 MIDI/MPE Tab | TODO | Pending verification. |
| F0674 | 679 | 3 | 30.2.6.1 The Global Section | TODO | Pending verification. |
| F0675 | 680 | 2 | 30.2.7 Sound Design Tips | TODO | Pending verification. |
| F0676 | 681-688 | 1 | 30.3 Drift | TODO | Pending verification. |
| F0677 | 681 | 2 | 30.3.1 Subtractive Synthesis | TODO | Pending verification. |
| F0678 | 682-683 | 2 | 30.3.2 Oscillator Section | TODO | Pending verification. |
| F0679 | 682 | 3 | 30.3.2.1 Oscillator 1 | TODO | Pending verification. |
| F0680 | 683 | 3 | 30.3.2.2 Oscillator 2 | TODO | Pending verification. |
| F0681 | 683 | 3 | 30.3.2.3 Pitch Mod | TODO | Pending verification. |
| F0682 | 683 | 3 | 30.3.2.4 Waveform Display | TODO | Pending verification. |
| F0683 | 683 | 3 | 30.3.2.5 Oscillator Mixer | TODO | Pending verification. |
| F0684 | 684 | 2 | 30.3.3 Filter Section | TODO | Pending verification. |
| F0685 | 685 | 2 | 30.3.4 Envelopes Section | TODO | Pending verification. |
| F0686 | 685 | 3 | 30.3.4.1 Envelope 1 | TODO | Pending verification. |
| F0687 | 686 | 3 | 30.3.4.2 Envelope 2 | TODO | Pending verification. |
| F0688 | 686 | 2 | 30.3.5 LFO Section | TODO | Pending verification. |
| F0689 | 687 | 2 | 30.3.6 Mod Section | TODO | Pending verification. |
| F0690 | 688 | 2 | 30.3.7 Global Section | TODO | Pending verification. |
| F0691 | 689-694 | 1 | 30.4 Drum Sampler | TODO | Pending verification. |
| F0692 | 689-690 | 2 | 30.4.1 Sample Controls Section | TODO | Pending verification. |
| F0693 | 691-692 | 2 | 30.4.2 Playback Effects Section | TODO | Pending verification. |
| F0694 | 693 | 2 | 30.4.3 Filter Section | TODO | Pending verification. |
| F0695 | 693 | 2 | 30.4.4 Global Section | TODO | Pending verification. |
| F0696 | 694 | 2 | 30.4.5 Context Menu Options for Drum Sampler | TODO | Pending verification. |
| F0697 | 695-699 | 1 | 30.5 Electric | TODO | Pending verification. |
| F0698 | 695 | 2 | 30.5.1 Architecture and Interface | TODO | Pending verification. |
| F0699 | 696 | 2 | 30.5.2 Hammer Section | TODO | Pending verification. |
| F0700 | 697 | 2 | 30.5.3 Fork Section | TODO | Pending verification. |
| F0701 | 698 | 2 | 30.5.4 Damper/Pickup Section | TODO | Pending verification. |
| F0702 | 698 | 3 | 30.5.4.1 Pickup Parameters | TODO | Pending verification. |
| F0703 | 698 | 3 | 30.5.4.2 Damper Parameters | TODO | Pending verification. |
| F0704 | 699 | 2 | 30.5.5 Global Section | TODO | Pending verification. |
| F0705 | 700-701 | 1 | 30.6 External Instrument | TODO | Pending verification. |
| F0706 | 702-703 | 1 | 30.7 Impulse | TODO | Pending verification. |
| F0707 | 702 | 2 | 30.7.1 Sample Slots | TODO | Pending verification. |
| F0708 | 703 | 2 | 30.7.2 Start, Transpose and Stretch | TODO | Pending verification. |
| F0709 | 703 | 2 | 30.7.3 Filter | TODO | Pending verification. |
| F0710 | 703 | 2 | 30.7.4 Saturator and Envelope | TODO | Pending verification. |
| F0711 | 703 | 2 | 30.7.5 Pan and Volume | TODO | Pending verification. |
| F0712 | 704 | 2 | 30.7.6 Global Controls | TODO | Pending verification. |
| F0713 | 704 | 2 | 30.7.7 Individual Outputs | TODO | Pending verification. |
| F0714 | 704-713 | 1 | 30.8 Meld | TODO | Pending verification. |
| F0715 | 704 | 2 | 30.8.1 General Overview | TODO | Pending verification. |
| F0716 | 705 | 2 | 30.8.2 Oscillators | TODO | Pending verification. |
| F0717 | 706-707 | 2 | 30.8.3 Oscillator Macros | TODO | Pending verification. |
| F0718 | 708 | 2 | 30.8.4 Envelopes Tab | TODO | Pending verification. |
| F0719 | 709 | 2 | 30.8.5 LFOs Tab | TODO | Pending verification. |
| F0720 | 709 | 2 | 30.8.6 Matrix Tab | TODO | Pending verification. |
| F0721 | 710 | 2 | 30.8.7 MIDI and MPE Tabs | TODO | Pending verification. |
| F0722 | 710 | 2 | 30.8.8 Settings Tab | TODO | Pending verification. |
| F0723 | 711-712 | 2 | 30.8.9 Filters | TODO | Pending verification. |
| F0724 | 713 | 2 | 30.8.10 Mix Section | TODO | Pending verification. |
| F0725 | 713 | 2 | 30.8.11 Global Controls | TODO | Pending verification. |
| F0726 | 714-731 | 1 | 30.9 Operator | TODO | Pending verification. |
| F0727 | 715 | 2 | 30.9.1 General Overview | TODO | Pending verification. |
| F0728 | 716-717 | 2 | 30.9.2 Oscillator Section | TODO | Pending verification. |
| F0729 | 716 | 3 | 30.9.2.1 Built-in Waveforms | TODO | Pending verification. |
| F0730 | 716 | 3 | 30.9.2.2 User Waveforms | TODO | Pending verification. |
| F0731 | 717 | 3 | 30.9.2.3 More Oscillator Parameters | TODO | Pending verification. |
| F0732 | 718 | 3 | 30.9.2.4 Aliasing | TODO | Pending verification. |
| F0733 | 718 | 2 | 30.9.3 LFO Section | TODO | Pending verification. |
| F0734 | 719-720 | 2 | 30.9.4 Envelopes | TODO | Pending verification. |
| F0735 | 721 | 2 | 30.9.5 Filter Section | TODO | Pending verification. |
| F0736 | 722 | 2 | 30.9.6 Global Controls | TODO | Pending verification. |
| F0737 | 723 | 2 | 30.9.7 Glide and Spread | TODO | Pending verification. |
| F0738 | 724 | 2 | 30.9.8 Strategies for Saving CPU Power | TODO | Pending verification. |
| F0739 | 724 | 2 | 30.9.9 Finally… | TODO | Pending verification. |
| F0740 | 724-731 | 2 | 30.9.10 The Complete Parameter List | TODO | Pending verification. |
| F0741 | 724 | 3 | 30.9.10.1 Global Shell and Display | TODO | Pending verification. |
| F0742 | 725 | 3 | 30.9.10.2 Modulation Targets | TODO | Pending verification. |
| F0743 | 726 | 3 | 30.9.10.3 Pitch Shell and Display | TODO | Pending verification. |
| F0744 | 727 | 3 | 30.9.10.4 Filter Shell and Display | TODO | Pending verification. |
| F0745 | 728 | 3 | 30.9.10.5 LFO Shell and Display | TODO | Pending verification. |
| F0746 | 729 | 3 | 30.9.10.6 Oscillators A-D Shell and Display | TODO | Pending verification. |
| F0747 | 730 | 3 | 30.9.10.7 Envelope Display | TODO | Pending verification. |
| F0748 | 731 | 3 | 30.9.10.8 Context Menu Options for Operator | TODO | Pending verification. |
| F0749 | 732-749 | 1 | 30.10 Sampler | TODO | Pending verification. |
| F0750 | 732 | 2 | 30.10.1 Getting Started with Sampler | TODO | Pending verification. |
| F0751 | 732 | 2 | 30.10.2 Multisampling | TODO | Pending verification. |
| F0752 | 733 | 2 | 30.10.3 Title Bar Options | TODO | Pending verification. |
| F0753 | 734 | 2 | 30.10.4 Sampler’s Tabs | TODO | Pending verification. |
| F0754 | 734-739 | 2 | 30.10.5 The Zone Tab | TODO | Pending verification. |
| F0755 | 735-736 | 3 | 30.10.5.1 Round Robin Sample Playback | TODO | Pending verification. |
| F0756 | 737 | 3 | 30.10.5.2 The Sample Layer List | TODO | Pending verification. |
| F0757 | 738 | 3 | 30.10.5.3 Key Zones | TODO | Pending verification. |
| F0758 | 739 | 3 | 30.10.5.4 Velocity Zones | TODO | Pending verification. |
| F0759 | 739 | 3 | 30.10.5.5 Sample Select Zones | TODO | Pending verification. |
| F0760 | 740-743 | 2 | 30.10.6 The Sample Tab | TODO | Pending verification. |
| F0761 | 741-743 | 3 | 30.10.6.1 Sample Playback | TODO | Pending verification. |
| F0762 | 744-745 | 2 | 30.10.7 The Pitch/Osc Tab | TODO | Pending verification. |
| F0763 | 744 | 3 | 30.10.7.1 The Modulation Oscillator (Osc) | TODO | Pending verification. |
| F0764 | 745 | 3 | 30.10.7.2 The Pitch Envelope | TODO | Pending verification. |
| F0765 | 746-747 | 2 | 30.10.8 The Filter/Global Tab | TODO | Pending verification. |
| F0766 | 746 | 3 | 30.10.8.1 The Filter | TODO | Pending verification. |
| F0767 | 747 | 3 | 30.10.8.2 The Volume Envelope and Global Controls | TODO | Pending verification. |
| F0768 | 748 | 2 | 30.10.9 The Modulation Tab | TODO | Pending verification. |
| F0769 | 748 | 3 | 30.10.9.1 The Auxiliary Envelope | TODO | Pending verification. |
| F0770 | 748 | 3 | 30.10.9.2 LFOs 1, 2 and 3 | TODO | Pending verification. |
| F0771 | 749 | 2 | 30.10.10 The MIDI Tab | TODO | Pending verification. |
| F0772 | 750 | 2 | 30.10.11 Importing Third-Party Multisamples | TODO | Pending verification. |
| F0773 | 750-760 | 1 | 30.11 Simpler | TODO | Pending verification. |
| F0774 | 751-754 | 2 | 30.11.1 Playback Modes | TODO | Pending verification. |
| F0775 | 752-753 | 3 | 30.11.1.1 Classic Playback Mode | TODO | Pending verification. |
| F0776 | 754 | 3 | 30.11.1.2 One-Shot Playback Mode | TODO | Pending verification. |
| F0777 | 754 | 3 | 30.11.1.3 Slicing Playback Mode | TODO | Pending verification. |
| F0778 | 755 | 2 | 30.11.2 Warp Controls | TODO | Pending verification. |
| F0779 | 756 | 2 | 30.11.3 Filter | TODO | Pending verification. |
| F0780 | 757 | 2 | 30.11.4 Envelopes | TODO | Pending verification. |
| F0781 | 758 | 2 | 30.11.5 LFO | TODO | Pending verification. |
| F0782 | 759 | 2 | 30.11.6 Global Parameters | TODO | Pending verification. |
| F0783 | 760 | 2 | 30.11.7 Context Menu Options for Simpler | TODO | Pending verification. |
| F0784 | 760 | 2 | 30.11.8 Strategies for Saving CPU Power | TODO | Pending verification. |
| F0785 | 761-772 | 1 | 30.12 Tension | TODO | Pending verification. |
| F0786 | 761 | 2 | 30.12.1 Architecture and Interface | TODO | Pending verification. |
| F0787 | 762-767 | 2 | 30.12.2 String Tab | TODO | Pending verification. |
| F0788 | 762 | 3 | 30.12.2.1 The Exciter Section | TODO | Pending verification. |
| F0789 | 762 | 3 | 30.12.2.2 Exciter Types | TODO | Pending verification. |
| F0790 | 763 | 3 | 30.12.2.3 Exciter Parameters | TODO | Pending verification. |
| F0791 | 764-765 | 3 | 30.12.2.4 The Damper Section | TODO | Pending verification. |
| F0792 | 766 | 3 | 30.12.2.5 The Termination Section | TODO | Pending verification. |
| F0793 | 767 | 3 | 30.12.2.6 The Pickup Section | TODO | Pending verification. |
| F0794 | 768-771 | 2 | 30.12.3 Filter/Global Tab | TODO | Pending verification. |
| F0795 | 772 | 2 | 30.12.4 Sound Design Tips | TODO | Pending verification. |
| F0796 | 773-782 | 1 | 30.13 Wavetable | TODO | Pending verification. |
| F0797 | 773 | 2 | 30.13.1 Wavetable Synthesis | TODO | Pending verification. |
| F0798 | 773-774 | 2 | 30.13.2 Oscillators | TODO | Pending verification. |
| F0799 | 775 | 2 | 30.13.3 Sub Oscillator | TODO | Pending verification. |
| F0800 | 775-776 | 2 | 30.13.4 Filters | TODO | Pending verification. |
| F0801 | 777 | 2 | 30.13.5 Matrix Tab | TODO | Pending verification. |
| F0802 | 778-779 | 2 | 30.13.6 Mod Sources Tab | TODO | Pending verification. |
| F0803 | 779 | 3 | 30.13.6.1 LFOs | TODO | Pending verification. |
| F0804 | 780 | 2 | 30.13.7 MIDI Tab | TODO | Pending verification. |
| F0805 | 780-781 | 2 | 30.13.8 Global and Unison Controls | TODO | Pending verification. |
| F0806 | 782 | 2 | 30.13.9 Hi-Quality Mode | TODO | Pending verification. |
| F0807 | 783-788 | 0 | 31. Max for Live | TODO | Pending verification. |
| F0808 | 783 | 1 | 31.1 Setting Up Max for Live | TODO | Pending verification. |
| F0809 | 784 | 1 | 31.2 Using Max for Live Devices | TODO | Pending verification. |
| F0810 | 784-786 | 1 | 31.3 Editing Max for Live Devices | TODO | Pending verification. |
| F0811 | 787 | 1 | 31.4 Building Max for Live MIDI Tools | TODO | Pending verification. |
| F0812 | 788 | 1 | 31.5 Max Dependencies | TODO | Pending verification. |
| F0813 | 788 | 1 | 31.6 Learning Max Programming | TODO | Pending verification. |
| F0814 | 789-823 | 0 | 32. Max for Live Devices | TODO | Pending verification. |
| F0815 | 790-797 | 1 | 32.1 Max for Live Instruments | TODO | Pending verification. |
| F0816 | 790 | 2 | 32.1.1 DS Clang | TODO | Pending verification. |
| F0817 | 791 | 2 | 32.1.2 DS Clap | TODO | Pending verification. |
| F0818 | 792 | 2 | 32.1.3 DS Cymbal | TODO | Pending verification. |
| F0819 | 793 | 2 | 32.1.4 DS FM | TODO | Pending verification. |
| F0820 | 794 | 2 | 32.1.5 DS HH | TODO | Pending verification. |
| F0821 | 795 | 2 | 32.1.6 DS Kick | TODO | Pending verification. |
| F0822 | 796 | 2 | 32.1.7 DS Snare | TODO | Pending verification. |
| F0823 | 797 | 2 | 32.1.8 DS Tom | TODO | Pending verification. |
| F0824 | 798-806 | 1 | 32.2 Max for Live Audio Effects | TODO | Pending verification. |
| F0825 | 798 | 2 | 32.2.1 Align Delay | TODO | Pending verification. |
| F0826 | 799-801 | 2 | 32.2.2 Envelope Follower | TODO | Pending verification. |
| F0827 | 802-804 | 2 | 32.2.3 LFO | TODO | Pending verification. |
| F0828 | 805-806 | 2 | 32.2.4 Shaper | TODO | Pending verification. |
| F0829 | 807-823 | 1 | 32.3 Max for Live MIDI Effects | TODO | Pending verification. |
| F0830 | 807-809 | 2 | 32.3.1 Envelope MIDI | TODO | Pending verification. |
| F0831 | 810-811 | 2 | 32.3.2 Expression Control | TODO | Pending verification. |
| F0832 | 812-813 | 2 | 32.3.3 MIDI Monitor | TODO | Pending verification. |
| F0833 | 814-819 | 2 | 32.3.4 MPE Control | TODO | Pending verification. |
| F0834 | 816 | 3 | 32.3.4.1 Press | TODO | Pending verification. |
| F0835 | 817 | 3 | 32.3.4.2 Slide | TODO | Pending verification. |
| F0836 | 818-819 | 3 | 32.3.4.3 NotePB | TODO | Pending verification. |
| F0837 | 820 | 2 | 32.3.5 Note Echo | TODO | Pending verification. |
| F0838 | 821-823 | 2 | 32.3.6 Shaper MIDI | TODO | Pending verification. |
| F0839 | 824-832 | 0 | 33. MIDI and Key Remote Control | TODO | Pending verification. |
| F0840 | 824-827 | 1 | 33.1 MIDI Remote Control | TODO | Pending verification. |
| F0841 | 825 | 2 | 33.1.1 Natively Supported Control Surfaces | TODO | Pending verification. |
| F0842 | 825 | 3 | 33.1.1.1 Instant Mappings | TODO | Pending verification. |
| F0843 | 826 | 2 | 33.1.2 Manual Control Surface Setup | TODO | Pending verification. |
| F0844 | 827 | 2 | 33.1.3 Takeover Mode | TODO | Pending verification. |
| F0845 | 828-832 | 1 | 33.2 The Mapping Browser | TODO | Pending verification. |
| F0846 | 829 | 2 | 33.2.1 Assigning MIDI Remote Control | TODO | Pending verification. |
| F0847 | 829 | 2 | 33.2.2 Mapping to MIDI Notes | TODO | Pending verification. |
| F0848 | 829 | 2 | 33.2.3 Mapping to Absolute MIDI Controllers | TODO | Pending verification. |
| F0849 | 830-831 | 2 | 33.2.4 Mapping to Relative MIDI Controllers | TODO | Pending verification. |
| F0850 | 831 | 3 | 33.2.4.1 Relative Session View Navigation | TODO | Pending verification. |
| F0851 | 831 | 3 | 33.2.4.2 Mapping to Clip View Controls | TODO | Pending verification. |
| F0852 | 832 | 2 | 33.2.5 Computer Keyboard Remote Control | TODO | Pending verification. |
| F0853 | 833-872 | 0 | 34. Using Push 1 | TODO | Pending verification. |
| F0854 | 833 | 1 | 34.1 Setup | TODO | Pending verification. |
| F0855 | 834 | 1 | 34.2 Browsing and Loading Sounds | TODO | Pending verification. |
| F0856 | 835-842 | 1 | 34.3 Playing and Programming Beats | TODO | Pending verification. |
| F0857 | 835-836 | 2 | 34.3.1 Loop Selector | TODO | Pending verification. |
| F0858 | 837 | 2 | 34.3.2 16 Velocities Mode | TODO | Pending verification. |
| F0859 | 837 | 2 | 34.3.3 64-Pad Mode | TODO | Pending verification. |
| F0860 | 837 | 2 | 34.3.4 Loading Individual Drums | TODO | Pending verification. |
| F0861 | 838 | 3 | 34.3.4.1 Additional Pad Options for Push 1 | TODO | Pending verification. |
| F0862 | 838-839 | 2 | 34.3.5 Step Sequencing Beats | TODO | Pending verification. |
| F0863 | 840-841 | 2 | 34.3.6 Real-time Recording | TODO | Pending verification. |
| F0864 | 842 | 2 | 34.3.7 Fixed Length Recording | TODO | Pending verification. |
| F0865 | 843-844 | 1 | 34.4 Additional Recording Options | TODO | Pending verification. |
| F0866 | 843 | 2 | 34.4.1 Recording with Repeat | TODO | Pending verification. |
| F0867 | 844 | 2 | 34.4.2 Quantizing | TODO | Pending verification. |
| F0868 | 845-847 | 1 | 34.5 Playing Melodies and Harmonies | TODO | Pending verification. |
| F0869 | 847 | 2 | 34.5.1 Playing in Other Keys | TODO | Pending verification. |
| F0870 | 848-850 | 1 | 34.6 Step Sequencing Melodies and Harmonies | TODO | Pending verification. |
| F0871 | 850 | 2 | 34.6.1 Adjusting the Loop Length | TODO | Pending verification. |
| F0872 | 851 | 1 | 34.7 Melodic Sequencer + 32 Notes | TODO | Pending verification. |
| F0873 | 851 | 2 | 34.7.1 32 Notes | TODO | Pending verification. |
| F0874 | 852 | 2 | 34.7.2 Sequencer | TODO | Pending verification. |
| F0875 | 852 | 1 | 34.8 Navigating in Note Mode | TODO | Pending verification. |
| F0876 | 853 | 1 | 34.9 Controlling Live’s Instruments and Effects | TODO | Pending verification. |
| F0877 | 854-855 | 1 | 34.10 Mixing with Push 1 | TODO | Pending verification. |
| F0878 | 856 | 1 | 34.11 Recording Automation | TODO | Pending verification. |
| F0879 | 857 | 1 | 34.12 Step Sequencing Automation | TODO | Pending verification. |
| F0880 | 857 | 2 | 34.12.1 Note-Specific Parameters | TODO | Pending verification. |
| F0881 | 858 | 2 | 34.12.2 Per-Step Automation | TODO | Pending verification. |
| F0882 | 858-859 | 1 | 34.13 Controlling Live’s Session View | TODO | Pending verification. |
| F0883 | 859 | 2 | 34.13.1 Session Overview | TODO | Pending verification. |
| F0884 | 860-861 | 1 | 34.14 Setting User Preferences | TODO | Pending verification. |
| F0885 | 862-872 | 1 | 34.15 Push 1 Control Reference | TODO | Pending verification. |
| F0886 | 862 | 2 | 34.15.0.1 Focus/Navigation Section | TODO | Pending verification. |
| F0887 | 863 | 2 | 34.15.0.2 Add Section | TODO | Pending verification. |
| F0888 | 864 | 2 | 34.15.0.3 Note Section | TODO | Pending verification. |
| F0889 | 865 | 2 | 34.15.0.4 State Control Section | TODO | Pending verification. |
| F0890 | 865 | 2 | 34.15.0.5 Selection Control Section | TODO | Pending verification. |
| F0891 | 865-866 | 2 | 34.15.0.6 Display/Encoder Section | TODO | Pending verification. |
| F0892 | 867 | 2 | 34.15.0.7 Tempo Section | TODO | Pending verification. |
| F0893 | 868 | 2 | 34.15.0.8 Edit Section | TODO | Pending verification. |
| F0894 | 869 | 2 | 34.15.0.9 Transport Section | TODO | Pending verification. |
| F0895 | 870 | 2 | 34.15.0.10 Touch Strip | TODO | Pending verification. |
| F0896 | 871 | 2 | 34.15.0.11 Pad Section | TODO | Pending verification. |
| F0897 | 872 | 2 | 34.15.0.12 Scene/Grid Section | TODO | Pending verification. |
| F0898 | 872 | 2 | 34.15.0.13 Using Footswitches with Push 1 | TODO | Pending verification. |
| F0899 | 873-931 | 0 | 35. Using Push 2 | TODO | Pending verification. |
| F0900 | 874 | 1 | 35.1 Setup | TODO | Pending verification. |
| F0901 | 874-876 | 1 | 35.2 Browsing and Loading Sounds | TODO | Pending verification. |
| F0902 | 877-888 | 1 | 35.3 Playing and Programming Beats | TODO | Pending verification. |
| F0903 | 877-878 | 2 | 35.3.1 Loop Selector | TODO | Pending verification. |
| F0904 | 879 | 2 | 35.3.2 16 Velocities Mode | TODO | Pending verification. |
| F0905 | 879 | 2 | 35.3.3 64-Pad Mode | TODO | Pending verification. |
| F0906 | 880-882 | 2 | 35.3.4 Loading Individual Drums | TODO | Pending verification. |
| F0907 | 881-882 | 3 | 35.3.4.1 Additional Pad Options for Push 2 | TODO | Pending verification. |
| F0908 | 883-885 | 2 | 35.3.5 Step Sequencing Beats | TODO | Pending verification. |
| F0909 | 886-887 | 2 | 35.3.6 Real-time Recording | TODO | Pending verification. |
| F0910 | 888 | 2 | 35.3.7 Fixed Length Recording | TODO | Pending verification. |
| F0911 | 889-890 | 1 | 35.4 Additional Recording Options | TODO | Pending verification. |
| F0912 | 889 | 2 | 35.4.1 Recording with Repeat | TODO | Pending verification. |
| F0913 | 890 | 2 | 35.4.2 Quantizing | TODO | Pending verification. |
| F0914 | 891 | 2 | 35.4.3 Arrangement Recording | TODO | Pending verification. |
| F0915 | 891-894 | 1 | 35.5 Playing Melodies and Harmonies | TODO | Pending verification. |
| F0916 | 894 | 2 | 35.5.1 Playing in Other Keys | TODO | Pending verification. |
| F0917 | 895-897 | 1 | 35.6 Step Sequencing Melodies and Harmonies | TODO | Pending verification. |
| F0918 | 897 | 2 | 35.6.1 Adjusting the Loop Length | TODO | Pending verification. |
| F0919 | 898-900 | 1 | 35.7 Melodic Sequencer + 32 Notes | TODO | Pending verification. |
| F0920 | 899 | 2 | 35.7.1 32 Notes | TODO | Pending verification. |
| F0921 | 899-900 | 2 | 35.7.2 Sequencer | TODO | Pending verification. |
| F0922 | 901-906 | 1 | 35.8 Working with Samples | TODO | Pending verification. |
| F0923 | 902 | 2 | 35.8.1 Classic Playback Mode | TODO | Pending verification. |
| F0924 | 903-904 | 2 | 35.8.2 One-Shot Mode | TODO | Pending verification. |
| F0925 | 904 | 3 | 35.8.2.1 Legato Playback | TODO | Pending verification. |
| F0926 | 905-906 | 2 | 35.8.3 Slicing Mode | TODO | Pending verification. |
| F0927 | 907 | 1 | 35.9 Navigating in Note Mode | TODO | Pending verification. |
| F0928 | 908-912 | 1 | 35.10 Working With Instruments and Effects | TODO | Pending verification. |
| F0929 | 910 | 2 | 35.10.1 Adding, Deleting, and Reordering Devices | TODO | Pending verification. |
| F0930 | 911-912 | 2 | 35.10.2 Working with Racks | TODO | Pending verification. |
| F0931 | 913-915 | 1 | 35.11 Track Control And Mixing | TODO | Pending verification. |
| F0932 | 915 | 2 | 35.11.1 Rack and Group Track Mixing | TODO | Pending verification. |
| F0933 | 916 | 1 | 35.12 Recording Automation | TODO | Pending verification. |
| F0934 | 917 | 1 | 35.13 Step Sequencing Automation | TODO | Pending verification. |
| F0935 | 918-921 | 1 | 35.14 Clip Mode | TODO | Pending verification. |
| F0936 | 920 | 2 | 35.14.1 Using MIDI Tracks in Clip Mode | TODO | Pending verification. |
| F0937 | 920 | 2 | 35.14.2 Real-Time Playing Layouts | TODO | Pending verification. |
| F0938 | 920-921 | 2 | 35.14.3 Sequencing Layouts | TODO | Pending verification. |
| F0939 | 921 | 3 | 35.14.3.1 Melodic Sequencer | TODO | Pending verification. |
| F0940 | 921 | 3 | 35.14.3.2 Melodic Sequencer + 32 Notes | TODO | Pending verification. |
| F0941 | 922 | 2 | 35.14.4 Note-Specific Parameters | TODO | Pending verification. |
| F0942 | 922-924 | 1 | 35.15 Controlling Live’s Session View | TODO | Pending verification. |
| F0943 | 924 | 2 | 35.15.1 Session Overview | TODO | Pending verification. |
| F0944 | 925 | 1 | 35.16 Setup Menu | TODO | Pending verification. |
| F0945 | 926-931 | 1 | 35.17 Push 2 Control Reference | TODO | Pending verification. |
| F0946 | 931 | 2 | 35.17.0.1 Using Footswitches with Push 2 | TODO | Pending verification. |
| F0947 | 932-940 | 0 | 36. Synchronizing with Link, Tempo Follower, and MIDI | TODO | Pending verification. |
| F0948 | 932-935 | 1 | 36.1 Synchronizing via Link | TODO | Pending verification. |
| F0949 | 932-934 | 2 | 36.1.1 Setting up Link | TODO | Pending verification. |
| F0950 | 935 | 2 | 36.1.2 Using Link | TODO | Pending verification. |
| F0951 | 935 | 2 | 36.1.3 Using Link Audio | TODO | Pending verification. |
| F0952 | 936-937 | 1 | 36.2 Synchronizing via Tempo Follower | TODO | Pending verification. |
| F0953 | 937 | 2 | 36.2.1 Setting Up Tempo Follower | TODO | Pending verification. |
| F0954 | 938-940 | 1 | 36.3 Synchronizing via MIDI | TODO | Pending verification. |
| F0955 | 938 | 2 | 36.3.1 Synchronizing External MIDI Devices to Live | TODO | Pending verification. |
| F0956 | 938 | 2 | 36.3.2 Synchronizing Live to External MIDI Devices | TODO | Pending verification. |
| F0957 | 939 | 3 | 36.3.2.1 MIDI Timecode Options | TODO | Pending verification. |
| F0958 | 939-940 | 2 | 36.3.3 Sync Delay | TODO | Pending verification. |
| F0959 | 941-946 | 0 | 37. Computer Audio Resources and Strategies | TODO | Pending verification. |
| F0960 | 941-944 | 1 | 37.1 Managing the CPU Load | TODO | Pending verification. |
| F0961 | 941-942 | 2 | 37.1.1 The CPU Load Meter | TODO | Pending verification. |
| F0962 | 943 | 2 | 37.1.2 CPU Load from Multichannel Audio | TODO | Pending verification. |
| F0963 | 943 | 2 | 37.1.3 CPU Load from Tracks and Devices | TODO | Pending verification. |
| F0964 | 944 | 2 | 37.1.4 Track Freeze | TODO | Pending verification. |
| F0965 | 945-946 | 1 | 37.2 Managing the Disk Load | TODO | Pending verification. |
| F0966 | 947-954 | 0 | 38. Audio Fact Sheet | TODO | Pending verification. |
| F0967 | 947 | 1 | 38.1 Testing and Methodology | TODO | Pending verification. |
| F0968 | 947-950 | 1 | 38.2 Neutral Operations | TODO | Pending verification. |
| F0969 | 948 | 2 | 38.2.1 Undithered Rendering | TODO | Pending verification. |
| F0970 | 948 | 2 | 38.2.2 Matching Sample Rate/No Transposition | TODO | Pending verification. |
| F0971 | 948 | 2 | 38.2.3 Unstretched Beats/Tones/Texture/Re-Pitch Warping | TODO | Pending verification. |
| F0972 | 949 | 2 | 38.2.4 Summing at Single Mix Points | TODO | Pending verification. |
| F0973 | 949 | 2 | 38.2.5 Recording External Signals (Bit Depth >/= A/D Converter) | TODO | Pending verification. |
| F0974 | 949 | 2 | 38.2.6 Recording Internal Sources at 32 Bit | TODO | Pending verification. |
| F0975 | 950 | 2 | 38.2.7 Freezing Tracks | TODO | Pending verification. |
| F0976 | 950 | 2 | 38.2.8 Bypassed Effects | TODO | Pending verification. |
| F0977 | 951 | 2 | 38.2.9 Routing | TODO | Pending verification. |
| F0978 | 951 | 2 | 38.2.10 Splitting Clips | TODO | Pending verification. |
| F0979 | 951-953 | 1 | 38.3 Non-Neutral Operations | TODO | Pending verification. |
| F0980 | 951 | 2 | 38.3.1 Playback in Complex and Complex Pro Mode | TODO | Pending verification. |
| F0981 | 952 | 2 | 38.3.2 Sample Rate Conversion/Transposition | TODO | Pending verification. |
| F0982 | 952 | 2 | 38.3.3 Volume Automation | TODO | Pending verification. |
| F0983 | 952 | 2 | 38.3.4 Dithering | TODO | Pending verification. |
| F0984 | 952 | 2 | 38.3.5 Recording External Signals (Bit Depth < A/D Converter) | TODO | Pending verification. |
| F0985 | 953 | 2 | 38.3.6 Recording Internal Sources Below 32 Bit | TODO | Pending verification. |
| F0986 | 953 | 2 | 38.3.7 Consolidate | TODO | Pending verification. |
| F0987 | 953 | 2 | 38.3.8 Clip Fades | TODO | Pending verification. |
| F0988 | 953 | 2 | 38.3.9 Panning | TODO | Pending verification. |
| F0989 | 953 | 2 | 38.3.10 Grooves | TODO | Pending verification. |
| F0990 | 954 | 1 | 38.4 Tips for Achieving Optimal Sound Quality in Live | TODO | Pending verification. |
| F0991 | 954 | 1 | 38.5 Conclusion | TODO | Pending verification. |
| F0992 | 955-960 | 0 | 39. MIDI Fact Sheet | TODO | Pending verification. |
| F0993 | 955 | 1 | 39.1 Ideal MIDI Behavior | TODO | Pending verification. |
| F0994 | 956 | 1 | 39.2 MIDI Timing Problems | TODO | Pending verification. |
| F0995 | 956 | 1 | 39.3 Live’s MIDI Solutions | TODO | Pending verification. |
| F0996 | 957-958 | 1 | 39.4 Variables Outside of Live’s Control | TODO | Pending verification. |
| F0997 | 959 | 1 | 39.5 Tips for Achieving Optimal MIDI Performance | TODO | Pending verification. |
| F0998 | 959-960 | 1 | 39.6 Summary and Conclusions | TODO | Pending verification. |
| F0999 | 961-971 | 0 | 40. Accessibility and Keyboard Navigation | TODO | Pending verification. |
| F1000 | 961-962 | 1 | 40.1 Menu and Keyboard Navigation Settings | TODO | Pending verification. |
| F1001 | 961 | 2 | 40.1.1 Using Tab for Navigation | TODO | Pending verification. |
| F1002 | 962 | 2 | 40.1.2 Settings Menu | TODO | Pending verification. |
| F1003 | 963 | 2 | 40.1.3 Options Menu | TODO | Pending verification. |
| F1004 | 963 | 2 | 40.1.4 Speak Help Text | TODO | Pending verification. |
| F1005 | 963 | 1 | 40.2 Audio Setup | TODO | Pending verification. |
| F1006 | 963 | 1 | 40.3 Connecting MIDI Devices | TODO | Pending verification. |
| F1007 | 964-968 | 1 | 40.4 Navigating in Live | TODO | Pending verification. |
| F1008 | 964-968 | 2 | 40.4.1 Navigate Menu | TODO | Pending verification. |
| F1009 | 964 | 3 | 40.4.1.1 Control Bar - Alt 0 (Win) / Option 0 (Mac) | TODO | Pending verification. |
| F1010 | 964 | 3 | 40.4.1.2 Session View - Alt 1 (Win) / Option 1 (Mac) | TODO | Pending verification. |
| F1011 | 965 | 3 | 40.4.1.3 Arrangement View - Alt 2 (Win) / Option 2 (Mac) | TODO | Pending verification. |
| F1012 | 966 | 3 | 40.4.1.4 Clip View - Alt 3 (Win) / Option 3 (Mac) | TODO | Pending verification. |
| F1013 | 967 | 3 | 40.4.1.5 Device View - Alt 4 (Win) / Option 4 (Mac) | TODO | Pending verification. |
| F1014 | 968 | 3 | 40.4.1.6 Browser - Alt 5 (Win) / Option 5 (Mac) | TODO | Pending verification. |
| F1015 | 968 | 3 | 40.4.1.7 Groove Pool - Alt 6 (Win) / Option 6 (Mac) | TODO | Pending verification. |
| F1016 | 969 | 3 | 40.4.1.8 Learn View - Alt 7 (Win) / Option 7 (Mac) | TODO | Pending verification. |
| F1017 | 969-971 | 1 | 40.5 Editing Automation and Modulation Envelopes | TODO | Pending verification. |
| F1018 | 969 | 2 | 40.5.1 Navigating Between Breakpoints | TODO | Pending verification. |
| F1019 | 970 | 2 | 40.5.2 Selecting and Editing Breakpoints | TODO | Pending verification. |
| F1020 | 971 | 2 | 40.5.3 Switching Between Automation Envelopes in Arrangement View | TODO | Pending verification. |
| F1021 | 972-994 | 0 | 41. Live Keyboard Shortcuts | TODO | Pending verification. |
| F1022 | 972 | 1 | 41.1 Showing and Hiding Views | TODO | Pending verification. |
| F1023 | 973 | 1 | 41.2 Keyboard Focus and Navigation | TODO | Pending verification. |
| F1024 | 974 | 1 | 41.3 Working with Sets and the Program | TODO | Pending verification. |
| F1025 | 975 | 1 | 41.4 Working with Devices and Plug-Ins | TODO | Pending verification. |
| F1026 | 975 | 1 | 41.5 Editing | TODO | Pending verification. |
| F1027 | 976 | 1 | 41.6 Adjusting Values | TODO | Pending verification. |
| F1028 | 977 | 1 | 41.7 Commands for Breakpoint Envelopes | TODO | Pending verification. |
| F1029 | 978 | 1 | 41.8 Loop Brace and Start/End Markers | TODO | Pending verification. |
| F1030 | 978 | 1 | 41.9 Zooming, Display and Selections | TODO | Pending verification. |
| F1031 | 979 | 1 | 41.10 Clip View Editor View Modes | TODO | Pending verification. |
| F1032 | 980 | 1 | 41.11 Clip View Sample Editor | TODO | Pending verification. |
| F1033 | 980-982 | 1 | 41.12 Clip View MIDI Note Editor | TODO | Pending verification. |
| F1034 | 983 | 1 | 41.13 Grid Snapping and Drawing | TODO | Pending verification. |
| F1035 | 983 | 1 | 41.14 Global Quantization | TODO | Pending verification. |
| F1036 | 984 | 1 | 41.15 Session View | TODO | Pending verification. |
| F1037 | 985-986 | 1 | 41.16 Arrangement View | TODO | Pending verification. |
| F1038 | 987 | 1 | 41.17 Comping | TODO | Pending verification. |
| F1039 | 987 | 1 | 41.18 Bounce to Audio | TODO | Pending verification. |
| F1040 | 988 | 1 | 41.19 Commands for Tracks | TODO | Pending verification. |
| F1041 | 989 | 1 | 41.20 Transport | TODO | Pending verification. |
| F1042 | 990 | 1 | 41.21 Audio Engine | TODO | Pending verification. |
| F1043 | 990 | 1 | 41.22 Browser | TODO | Pending verification. |
| F1044 | 991 | 1 | 41.23 Similar Sample Swapping | TODO | Pending verification. |
| F1045 | 991 | 1 | 41.24 Key/MIDI Map Mode and the Computer MIDI Keyboard | TODO | Pending verification. |
| F1046 | 992 | 1 | 41.25 Momentary Latching Shortcuts | TODO | Pending verification. |
| F1047 | 992-993 | 1 | 41.26 General Keyboard Navigation and Workflow | TODO | Pending verification. |
| F1048 | 993 | 2 | 41.26.1 Using Tab for Navigation | TODO | Pending verification. |
| F1049 | 993 | 2 | 41.26.2 Navigating Between Controls in the Settings Menu | TODO | Pending verification. |
| F1050 | 994 | 1 | 41.27 Editing Automation and Modulation Envelopes with the Keyboard | TODO | Pending verification. |
| F1051 | 994 | 1 | 41.28 Accessing Menus | TODO | Pending verification. |
| F1052 | 994 | 1 | 41.29 Using Live’s Context Menu | TODO | Pending verification. |
| F1053 | 995-997 | 0 | 42. Credits | TODO | Pending verification. |

## Page Extraction Ledger

Every PDF page has been extracted to `audit/manual_pages/page_####.txt` and logged in
`audit/manual_pages.jsonl` with page number, word count, character count, and text SHA-256.
The feature inventory above is seeded from the PDF outline; subsequent passes expand entries
where pages contain multiple distinct controls under one section.
