import os
import shutil

# Check if there are Excel files in the backup results
source_dir = 'temp_analysis_results/out_mean_based/'
dest_dir = 'analysis_results/'

files = os.listdir(source_dir)
excel_files = [f for f in files if f.endswith('.xlsx') and f.startswith('heat_')]

print(f'Found {len(excel_files)} Excel heat files in backup')

if excel_files:
    print('Copying Excel files...')
    for file in excel_files:
        if not file.startswith('heat_emp_') and file != 'heat_ALL.xlsx':  # Skip employment types
            src = os.path.join(source_dir, file)
            dst = os.path.join(dest_dir, file)
            shutil.copy2(src, dst)
            print(f'Copied {file}')
    
    print('\nRe-running shortage analysis...')
else:
    print('No Excel files found - the shortage analysis needs to be modified to use parquet files')