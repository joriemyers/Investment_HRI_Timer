# Investment_HRI_Timer

A Python-based participant timer GUI with a Lab Streaming Layer (LSL) bridge, designed for Human-Robot Interaction (HRI) research studies. The GUI manages a baseline period and four counterbalanced task trials per participant, streams real-time event markers over the network, and records event timing for within-trial task phases.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation and Setup](#installation-and-setup)
4. [Running the GUI](#running-the-gui)
5. [Session Flow](#session-flow)
6. [Trial Color Coding — NASA Orion RPL Standards](#trial-color-coding--nasa-orion-rpl-standards)
7. [Latin Square Counterbalancing](#latin-square-counterbalancing)
8. [Lab Streaming Layer (LSL)](#lab-streaming-layer-lsl)
9. [Recording Data with LabRecorder](#recording-data-with-labrecorder)
10. [Viewing Live Streams with StreamViewer](#viewing-live-streams-with-streamviewer)
11. [Reading XDF Files After Recording](#reading-xdf-files-after-recording)
12. [LSL Markers Reference](#lsl-markers-reference)
13. [Troubleshooting](#troubleshooting)

---

## Features

- Participant login screen with ID validation (101–110)
- 2-minute baseline timer before trials begin
- Four counterbalanced task trials per participant using a Latin Square design
- Trials A and C are 15 minutes; Trials B and D are 30 minutes
- Sequential trial flow with locked Next button (cannot advance until timer completes or is stopped)
- Clock turns red when 5 minutes remain on any timer
- Event marker buttons during trials: Leak Check, Visual Inspection, and Stop - each recording the elapsed time from the previous event
- Session Complete screen at the end of each participant session
- Full LSL integration streaming named string markers over the local network in real time

---

## Requirements

- Python 3.8 or higher
- `tkinter` - included with Python on Windows by default
- `pylsl` - the Python interface for the Lab Streaming Layer

---

## Installation and Setup

Follow these steps from scratch on a Windows computer.

### Step 1 - Install Python

If you do not already have Python installed, download it from [python.org](https://www.python.org/downloads/). Choose the latest stable version (3.10 or higher recommended). During installation, check the box that says **"Add Python to PATH"** before clicking Install.

To verify the installation, open PowerShell and run:

```
python --version
```

### Step 2 - Install Git

Git is needed to push your project to GitHub. Check if it is installed by running:

```
git --version
```

If you get an error, download and install Git from [git-scm.com](https://git-scm.com). Use all default options during installation, then close and reopen PowerShell.

### Step 3 - Create your project folder

In PowerShell, run:

```
cd C:\Users\$env:USERNAME\Documents
mkdir Investment_HRI_Timer
cd Investment_HRI_Timer
```

### Step 4 - Add the project files

Copy `timer_gui.py` and `requirements.txt` into the `Investment_HRI_Timer` folder you just created. You can drag and drop them from your Downloads folder into the project folder in File Explorer.

### Step 5 - Install pylsl

In PowerShell, from inside your project folder, run:

```
pip install pylsl
```

This installs the Python interface for the Lab Streaming Layer, which enables the GUI to broadcast event markers over the network.

### Step 6 - Create a GitHub repository

1. Go to [github.com](https://github.com) and sign in or create a free account
2. Click the **+** icon in the top right corner and select **New repository**
3. Name it `Investment_HRI_Timer`
4. Set it to **Public**
5. Do **not** check "Add a README file" since one is already included
6. Click **Create repository**

### Step 7 - Push your files to GitHub

In PowerShell, from inside your project folder:

```
git init
git add .
git commit -m "Initial commit: HRI timer GUI with LSL bridge"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Investment_HRI_Timer.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username. When prompted for a password, GitHub requires a Personal Access Token - you can generate one at GitHub → Settings → Developer Settings → Personal Access Tokens.

---

## Running the GUI

In PowerShell, navigate to your project folder and run:

```
python timer_gui.py
```

The login screen will appear. Enter a participant ID between 101 and 110 and click **Begin Session**.

---

## Session Flow

Each participant session follows this sequence:

1. **Login** - Enter participant ID (101–110). The GUI validates the ID and automatically loads the correct Latin Square trial order for that participant.
2. **Baseline** - A 2-minute timer runs. The experimenter clicks Start when ready. When the timer completes, the Next button unlocks.
3. **Trial 1 through Trial 4** - Each trial screen loads automatically in the counterbalanced order for that participant. The timer duration is determined by the condition (15 min for A and C, 30 min for B and D). During each trial, three event buttons appear in sequence: Leak Check, Visual Inspection, and Stop. Each button unlocks only after the previous one has been pressed, and each records the elapsed time from the prior event.
4. **Session Complete** - A confirmation screen appears. The experimenter can start a new participant session from this screen.

---

## Trial Color Coding - NASA Orion RPL Standards

The four trial conditions are each assigned a distinct color in the GUI. These colors were selected in accordance with NASA's Orion Rapid Prototyping Lab (RPL) human factors display standards, which emphasize using perceptually distinct, unambiguous colors in operator interfaces to prevent confusion and reduce the risk of misinterpretation during tasks. The RPL standards call for colors that are clearly separable from one another across a range of lighting conditions and that avoid pairing colors that are commonly confused by individuals with color vision deficiencies.

The selected colors and their rationale are:

| Trial | Color | Hex Code | Rationale |
|-------|-------|----------|-----------|
| A | Orange | `#FF8200` | High-visibility warm tone; clearly distinct from cool hues; commonly used in aerospace interfaces as an attention color that stops short of indicating an error state |
| B | Dodger Blue | `#1E90FF` | A saturated cool blue that contrasts strongly with orange and pink; widely used in NASA display systems as a neutral informational color |
| C | Hot Pink | `#FF69B4` | A vivid warm-cool intermediate that is perceptually distinct from orange, blue, and purple; sufficiently saturated to avoid confusion with skin-tone adjacent neutrals |
| D | Medium Purple | `#9370DB` | A mid-range purple with enough saturation to stand apart from blue and pink while remaining clearly distinguishable in low-contrast viewing conditions |

These four colors were chosen specifically to avoid placing spectrally adjacent hues next to one another (for example, avoiding red next to orange, or lavender next to light blue) and to maintain clear separability for the most common forms of color vision deficiency. This approach aligns with the NASA Ames color usage guidelines for information visualization, which advise using no more than four to six distinct categorical colors and ensuring that color is never the sole encoding of critical information.

---

## Latin Square Counterbalancing

### Why counterbalancing is necessary

If every participant completed the four trials in the same order (for example, always A → B → C → D), any differences you measure between conditions could be partly or entirely due to order effects rather than the conditions themselves. Participants may perform differently on a task simply because it is their first trial and they are still learning, or because they are fatigued by the time they reach the fourth trial. Counterbalancing controls for this by systematically varying the trial order across participants so that each condition appears in each position an equal (or near-equal) number of times.

### How a Latin Square works

A Latin Square is a grid in which every item appears exactly once in each row and exactly once in each column. For four conditions, a 4×4 Latin Square looks like this:

```
         Position 1   Position 2   Position 3   Position 4
Row 1:       A            B            D            C
Row 2:       B            C            A            D
Row 3:       C            D            B            A
Row 4:       D            A            C            B
```

Each condition (A, B, C, D) appears in each position (1st, 2nd, 3rd, 4th) exactly once across the four rows. This ensures that across participants assigned to different rows, no condition is systematically always first, always second, and so on.

### Balanced Latin Square

The specific ordering used here is a **balanced Latin Square**, which goes one step further than a standard Latin Square. In addition to each condition appearing in each position once, a balanced Latin Square also controls for **carry-over effects** , meaning the influence that one condition may have on the next. The sequence follows a specific construction formula (positions: 1, 2, 4, 3, then each subsequent row shifts all conditions forward by one), which is the standard method used in experimental psychology to achieve carry-over balance.

### Participant-to-row assignment

| Participant ID | Latin Square Row | Trial Order |
|----------------|-----------------|-------------|
| 101, 105, 109 | Row 1 | A → B → D → C |
| 102, 106, 110 | Row 2 | B → C → A → D |
| 103, 107 | Row 3 | C → D → B → A |
| 104, 108 | Row 4 | D → A → C → B |

With 10 participants and only 4 unique rows, the pattern cycles through the square twice with two additional participants (109 and 110) repeating the first two rows. This is standard practice when the number of participants is not an exact multiple of the number of conditions. The design remains as balanced as possible given the constraint.

The GUI automatically determines the correct trial order when the participant ID is entered at the login screen. No manual setup is required between participants.

---

## Lab Streaming Layer (LSL)

### What LSL is

The Lab Streaming Layer (LSL) is an open-source software framework developed for the unified collection of time series data in research experiments. It handles networking, time synchronization, near-real-time data access, and optional centralized recording of data streams across multiple devices and applications simultaneously.

LSL was built specifically for neurophysiological and behavioral research applications where precise timing is critical. It allows multiple data streams from different sources, such as EEG amplifiers, eye trackers, motion capture systems, and stimulus presentation software, to be collected simultaneously with millisecond-level synchronization, even when those devices are running on different computers and using different internal clocks.

### How LSL works

LSL operates on a **publish-subscribe** model over a local area network (LAN). Any application that has data to share creates an **outlet** and broadcasts it onto the network. Any application that wants to receive that data creates an **inlet** and subscribes to the stream. Streams are discovered automatically using service discovery; no manual IP address configuration is required as long as all devices are on the same network.

Each stream consists of:

- **Samples** - individual measurements (in this project, string event markers)
- **Metadata** - an XML header describing the stream name, type, number of channels, sampling rate, and data format
- **Timestamps** - each sample is time-stamped automatically using LSL's built-in clock synchronization

LSL uses a time synchronization protocol based on the Network Time Protocol (NTP) to align timestamps across different machines. This means that even if your timer GUI is running on one computer and your recording software is running on another, the event markers can be precisely aligned in time with other data streams such as physiological signals.

### What LSL can be used for in HRI research

In the context of this study, LSL serves as a real-time event broadcast system. Every time a timer starts, stops, or completes, and every time an event marker button is pressed, a labeled string marker is sent over the network. These markers can be:

- Recorded alongside physiological data (EEG, ECG, EMG, eye tracking) to align behavioral events with biosignals
- Used to trigger other systems in real time (for example, starting a robot behavior or logging a video timestamp)
- Monitored live during a session using a stream viewer
- Stored to disk in XDF format for offline analysis

### LSL stream details for this project

| Property | Value |
|----------|-------|
| Stream name | `HRI_Timer_Events` |
| Stream type | `Markers` |
| Channel count | 1 |
| Channel format | String |
| Sample rate | Irregular (event-driven) |
| Source ID | `InvestmentHRI_001` |

---

## Recording Data with LabRecorder

LabRecorder is the standard recording application for LSL. It discovers all active LSL streams on the network and records them together into a single XDF file with synchronized timestamps.

### Setup

1. Download LabRecorder from the [releases page](https://github.com/labstreaminglayer/App-LabRecorder/releases). On Windows, download the file ending in `win_amd64.zip`.
2. Extract the zip file by right-clicking it and selecting **Extract All**.
3. Open the extracted folder and double-click `LabRecorder.exe`. If Windows shows a security warning, click **More Info** then **Run Anyway**.

### Recording a session

1. Launch `timer_gui.py` first so the LSL stream is active on the network.
2. Open LabRecorder.
3. Click the **Update** button in LabRecorder. The stream `HRI_Timer_Events` should appear in the stream list.
4. Check the checkbox next to `HRI_Timer_Events` to select it for recording.
5. Use the **Browse** button to choose where to save your XDF file.
6. Click **Start** in LabRecorder before beginning the participant session.
7. Run the participant through the full session in the timer GUI.
8. Click **Stop** in LabRecorder when the session is complete.

It is important to start LabRecorder recording **before** the participant session begins, and to stop it only after the session is fully complete, to avoid missing any markers.

---

## Viewing Live Streams with StreamViewer

StreamViewer is a lightweight tool that lets you see LSL markers arriving in real time during a session, without needing to record them. This is useful for confirming that the LSL bridge is working correctly and for monitoring events as they happen.

### Installing StreamViewer

StreamViewer is included in the pylsl Python package. You also need `pyqtgraph`. Install both with:

```
pip install pylsl pyqtgraph
```

### Launching StreamViewer

Make sure `timer_gui.py` is already running, then open a second PowerShell window and run:

```
python -m pylsl.StreamViewer
```

A window will open showing all active LSL streams on the network. Select `HRI_Timer_Events` from the list and click **Select**. You will see incoming markers displayed in real time as you interact with the timer GUI, for example, when you press Start on a timer or click an event button, the corresponding marker string will appear immediately in the StreamViewer window.

### What to look for

When the timer GUI is running and LSL is active, you should see the `HRI_Timer_Events` stream listed in StreamViewer. As you run through a session, markers such as `session_start_P101`, `P101_baseline_start`, `P101_trial1_A_start`, `P101_trial1_A_leak_check`, and so on will appear in the viewer window. If no stream appears, see the Troubleshooting section below.

---

## Reading XDF Files After Recording

XDF (Extensible Data Format) is the file format used by LabRecorder to store LSL streams. It stores all recorded streams together in a single file, with each sample paired with its precise timestamp. The format supports any number of simultaneous streams with different sampling rates and data types.

### Reading XDF files in Python

Install the `pyxdf` library:

```
pip install pyxdf
```

Then use the following script to load and inspect your recorded data:

```python
import pyxdf

# Load the XDF file
streams, header = pyxdf.load_xdf('path/to/your/recording.xdf')

# Find the HRI_Timer_Events stream
for stream in streams:
    if stream['info']['name'][0] == 'HRI_Timer_Events':
        print("Stream found!")
        timestamps = stream['time_stamps']
        markers    = stream['time_series']
        for ts, marker in zip(timestamps, markers):
            print(f"{ts:.4f}s  —  {marker[0]}")
```

This will print every marker with its precise timestamp, which you can then align with other data streams (such as physiological recordings) for analysis.

### Reading and viewing XDF files in MATLAB

This section walks through the full process of loading your XDF file in MATLAB and viewing your event markers in a readable table.

#### Step 1 - Download load_xdf

Download the `load_xdf.m` file from the [XDF MATLAB importer](https://github.com/xdf-modules/xdf-Matlab). On that page, click the green **Code** button and select **Download ZIP**. Extract the zip file somewhere easy to find, such as `C:\Users\YourName\Documents\xdf-Matlab`.

#### Step 2 - Add load_xdf to your MATLAB path

Open MATLAB and run the following, replacing the path with wherever you extracted the file:

```matlab
addpath('C:\Users\YourName\Documents\xdf-Matlab')
```

Confirm it worked by running:

```matlab
which load_xdf
```

This should print the full path to the `load_xdf.m` file. If it prints nothing, the path in your `addpath` command is incorrect, double check the folder location in File Explorer.

#### Step 3 - Load your XDF file

Use the file browser to select your XDF file without needing to type the path manually:

```matlab
[filename, pathname] = uigetfile('*.xdf', 'Select your XDF file');
fullpath = fullfile(pathname, filename);
streams = load_xdf(fullpath);
disp('File loaded successfully')
disp(length(streams))
```

A file browser window will open. Navigate to your XDF recording file (saved by LabRecorder, usually in your Documents folder), select it, and click **Open**. MATLAB will print `File loaded successfully` and the number of streams found in the file.

#### Step 4 - View your markers as a table

Run the following to display all event markers and their timestamps in a clean, readable table:

```matlab
% Pull out markers and timestamps from the first stream
timestamps = streams{1}.time_stamps';
markers    = streams{1}.time_series';

% Convert to relative time starting from zero
relative_time = timestamps - timestamps(1);

% Build the table
T = table(relative_time, timestamps, markers, ...
    'VariableNames', {'Time_From_Start_s', 'Raw_Timestamp', 'Marker'});

% Display in the command window
disp(T)
```

This prints a table with three columns: time from the start of the session in seconds, the raw LSL timestamp, and the marker name (such as `P101_trial1_A_leak_check`).

To open the table in MATLAB's interactive spreadsheet-style viewer where you can scroll through all rows, add this line:

```matlab
openvar('T')
```

This opens a separate window showing all your markers in a grid you can read and scroll through, similar to a spreadsheet.

---

## LSL Markers Reference

The following markers are sent during a session. `P###` refers to the participant ID (e.g., `P101`).

| Marker | When it is sent |
|--------|----------------|
| `session_start_P###` | Participant ID confirmed, session begins |
| `P###_baseline_start` | Baseline timer started |
| `P###_baseline_stop` | Baseline timer stopped manually |
| `P###_baseline_complete` | Baseline timer counted down to zero |
| `P###_baseline_5min_warning` | 5 minutes remaining on baseline (not applicable for 2-min baseline, but present in code) |
| `P###_trial#_X_start` | Trial timer started (# = trial number 1–4, X = condition A/B/C/D) |
| `P###_trial#_X_stop` | Trial timer stopped |
| `P###_trial#_X_complete` | Trial timer counted down to zero |
| `P###_trial#_X_5min_warning` | 5 minutes remaining on trial timer |
| `P###_trial#_X_leak_check` | Leak Check event button pressed |
| `P###_trial#_X_visual_inspection` | Visual Inspection event button pressed |
| `P###_trial#_X_event_stop` | Event Stop button pressed (also stops the timer) |
| `session_end_P###` | Session Complete screen reached |
| `app_closed` | GUI window closed |

---

## Troubleshooting

**`pylsl` import error when running the GUI**
Run `pip install pylsl` and try again. If the error persists, make sure you are running the same Python installation where you installed pylsl (check with `where python` in PowerShell).

**Stream does not appear in LabRecorder or StreamViewer**
- Make sure `timer_gui.py` is running before opening LabRecorder or StreamViewer
- Click the **Update** button in LabRecorder to refresh the stream list
- Ensure both applications are on the same network. If using Wi-Fi, verify both devices are connected to the same access point
- Check that your Windows Firewall is not blocking Python. Go to Windows Defender Firewall → Allow an app through the firewall → find Python and make sure both Private and Public are checked
- LSL uses UDP multicast on port 16571 for stream discovery. Some network configurations block multicast traffic

**`git push` asks for a password and fails**
GitHub no longer accepts account passwords for command-line pushes. You need a Personal Access Token. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate New Token. Give it `repo` scope, copy the token, and use it as your password when prompted.

**Timer GUI opens but shows "● LSL Offline"**
This means pylsl is not installed or could not be imported. Run `pip install pylsl` and restart the GUI.
