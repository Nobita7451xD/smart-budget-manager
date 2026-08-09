<img width="857" height="878" alt="Screenshot 2026-08-09 010327" src="https://github.com/user-attachments/assets/af0bda5e-fdaa-4c51-81fd-c9792c72f0c2" />
 # Smart Budget Manager v1.0

Single-window desktop finance tracker built with CustomTkinter and SQLite.

## Features

- Login/register and profile settings
- Income and expense CRUD: add, edit, delete and history
- Monthly budget, progress indicator and overspending warnings
- Live dashboard, financial totals and quick actions
- Spending reports: category pie chart and monthly spending chart
- CSV, Excel and PDF financial-report exports
- Currency, dark/light/system appearance settings and logout confirmation

## Run

Install Python 3.11 or newer, then run from the project folder:

```powershell
py -m pip install -r requirements.txt
py main.py
```

All data is saved locally in `finance.db`.

## Build a Windows executable

```powershell
py -m PyInstaller --noconfirm --onefile --windowed --name SmartBudgetManager main.py
```

The ready-to-share executable will be created in the `dist` folder.
