import os

# List of top-level galaxy directories
galaxies = [
    "ESO021", "ESO137", "MCG523", "NGC1079", "NGC1947", "NGC2992", "NGC3175",
    "NGC3749", "NGC4224", "NGC4260", "NGC5037", "NGC5506", "NGC5845", "NGC6814", "NGC718", "NGC7582",
    "ESO093", "ESO208", "MCG514", "MCG630", "NGC1315", "NGC1375", "NGC2110", "NGC3081", "NGC3717",
    "NGC3783", "NGC4235", "NGC4593", "NGC5128", "NGC5728", "NGC5921", "NGC7172", "NGC7213", "NGC7727"
]

# Root path where galaxy folders are located
root_dir = '/data/c3040163/llama/alma/raw/'  # <-- Replace with your actual root directory

calibrated_paths = []

for galaxy in galaxies:
    current_path = os.path.join(root_dir, galaxy)
    while True:
        try:
            # Get list of all subdirectories
            subdirs = [d for d in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, d))]
        except FileNotFoundError:
            print(f"Directory not found: {current_path}")
            break

        if 'calibrated' in subdirs:
            calibrated_paths.append(os.path.join(current_path, 'calibrated'))
            break
        elif len(subdirs) == 1:
            current_path = os.path.join(current_path, subdirs[0])
        else:
            print(f"Unexpected directory structure in {current_path}")
            break

# Print the full list
print(calibrated_paths)