# Investment_HRI_Timer

A Python-based participant GUI with a Lab Streaming Layer (LSL) bridge for HRI studies.

## Features

- **Baseline timer** — 2 minutes
- **15-minute task timer**
- **30-minute task timer**
- Each timer has independent Start, Stop, and Reset controls
- Live countdown display with progress bar
- LSL markers streamed over the network for every start/stop/complete event

## LSL Stream Details

| Property       | Value                  |
|----------------|------------------------|
| Stream name    | `HRI_Timer_Events`     |
| Stream type    | `Markers`              |
| Channel count  | 1 (string)             |
| Sample rate    | Irregular (event-driven)|

### Markers sent

| Event                  | Marker string          |
|------------------------|------------------------|
| Baseline started       | `baseline_start`       |
| Baseline stopped       | `baseline_stop`        |
| 15-min task started    | `task15_start`         |
| 15-min task stopped    | `task15_stop`          |
| 30-min task started    | `task30_start`         |
| 30-min task stopped    | `task30_stop`          |
| Any timer completes    | `timer_complete_<name>`|
| Window closed          | `session_end`          |

## Requirements

- Python 3.8+
- tkinter (included with Python on Windows)
- pylsl

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Investment_HRI_Timer.git
cd Investment_HRI_Timer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the GUI
python timer_gui.py
```

## Testing with LabRecorder

1. Download [LabRecorder](https://github.com/labstreaminglayer/App-LabRecorder/releases)
2. Launch `timer_gui.py` first
3. Open LabRecorder — the stream `HRI_Timer_Events` should appear in the stream list
4. Click **Start** on any timer to confirm markers are being received

## Troubleshooting

- **`pylsl` import error** — run `pip install pylsl`
- **Stream not visible in LabRecorder** — ensure both apps are on the same network/machine and no firewall is blocking UDP multicast (port 16571)
