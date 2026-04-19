# Tutorial: How to Add Support for a New Console

RetroAchievements supports dozens of systems. `ra-rom-manager` supports many out-of-the-box, but what if you want to add a brand new one (e.g., Nintendo GameCube)? 

Here is the step-by-step guide to adding a new console to the manager.

## Step 1: Find the Console ID
RetroAchievements tracks every console by a unique ID. 
1. Go to the[RetroAchievements API Documentation](https://retroachievements.org/APIv1.php#get-consoleid).
2. Look up your desired console. For Nintendo GameCube, the ID is **21** (Wait, GameCube actually might be a different ID, check the docs! Let's pretend it's `43`).

## Step 2: Update `config.py`
Open `src/ra_manager/config.py`. You need to tell the app the name of the console, and what folder name to look for.

1. Add it to `CONSOLES`:
```python
CONSOLES = {
    ...
    43: "GameCube",
}