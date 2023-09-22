from django.shortcuts import render

# Create your views here.
def crcl(request):
    return render(request,"crcl.html")
from django.shortcuts import render
import numpy as np
import pandas as pd

# Load the adjustment table from a CSV file
adjustment_table = pd.read_csv('myapp/adjustment_table.csv', sep=';', index_col='INR',decimal=',')

# Load the second table from a CSV file
dosage_table = pd.read_csv('myapp/dosage_table.csv', sep=';', index_col=0,decimal=',')

def distribute_tablets(total_tablets, length_of_schedule, divisibility):
    # Calculate the number of whole tablets and the fraction of a tablet
    whole_tablets, fraction = divmod(total_tablets, length_of_schedule)

    # Calculate the number of extra tablets that will be distributed
    extra_tablets = int(divisibility*(total_tablets-(length_of_schedule*whole_tablets)))

    # Convert length_of_schedule to an integer
    length_of_schedule = int(length_of_schedule)

    # Create a list representing the number of tablets for each day
    tablets_per_day = [whole_tablets] * length_of_schedule

    # Distribute the extra tablets evenly across the schedule
    for i in range(extra_tablets):
        # Calculate the index of the day that will receive the extra tablet
        index = i * length_of_schedule // extra_tablets

        # Add the extra tablet to the corresponding day
        tablets_per_day[index] += (1/divisibility)

    return tablets_per_day


def calculate_dosage(request):
    if request.method == 'POST':
        day_dosages = []
        for day in range(1, 8):
            dosage_key = f"day{day}_dosage"
            dosage = request.POST.get(dosage_key, '')
            if dosage:
                
                day_dosages.append(float(dosage))
        print(day_dosages)
        num_days = len(day_dosages)
        total_dosage = sum(day_dosages)
        mean_daily_dosage = total_dosage / num_days if num_days > 0 else 0
        old_dose = mean_daily_dosage

        medication = request.POST.get('medication', '')
        # med_dosage = request.POST.get('med_dosage', '')
        # med_dosage = float(med_dosage.replace(',', '.')) if med_dosage else 0.0  # Convert to float if not empty
        therapeutic_range = request.POST.get('therapeutic_range', '')
        
        user_choice = request.POST.get('divisibility', '')  # Get user's choice from form
        divisibility_options = {
            "quarter": 4,
            "half": 2,
            "whole": 1
        }
        divisibility = divisibility_options.get(user_choice, 1)  # Default to 1 if not found

        therapeutic_range = request.POST.get('therapeutic_range', '')
        
        str_inr = request.POST.get('inr_result')
        print(f"str inr {str_inr}")
        INR_result = round(float(str_inr), 1)

        range_values = therapeutic_range.split(' - ')
        print(f"ranges values {range_values}")
        if len(range_values) == 2:
            
            lower = float(range_values[0])
            upper = float(range_values[1])
            print(f"lower {lower}")
            print(f"upper {upper}")
            
        if lower <= INR_result <= upper:
            # The INR result is within the therapeutic range, no adjustment needed
            adjustment = 0
        else:
            # The INR result is outside the therapeutic range, look up the adjustment in the table
              # Load the adjustment table from a CSV file
            adjustment = adjustment_table.loc[INR_result, therapeutic_range]
            adjustment = float(adjustment.replace(',', '.').strip('%')) / 100  # Convert the percentage to a decimal


        # Apply the adjustment to the medication dosage
        adjusted_dosage = mean_daily_dosage * (1 + adjustment)
        new_dose = adjusted_dosage
        #let's start building our new medication shchedule
        # Convert the first column to numeric
        dosage_table.iloc[:, 0] = pd.to_numeric(dosage_table.iloc[:, 0])

        # Filter the DataFrame to keep only rows where the first column is divisible by divisibility
        filtered_dosage_table = dosage_table[dosage_table.iloc[:, 0] % divisibility == 0]

        
        
        difference = np.abs(filtered_dosage_table.values - adjusted_dosage)

        # Find the minimum difference
        min_difference = np.min(difference)

        # Find all locations where the difference is equal to the minimum difference
        locations = np.where(difference == min_difference)

        # Convert the locations to a list of tuples
        locations = list(zip(locations[0], locations[1]))

        # Sort the locations by total tablets and length of schedule
        locations.sort(key=lambda x: (filtered_dosage_table.index[x[0]], filtered_dosage_table.columns[x[1]]))

        # Get the location with the lowest total tablets and lowest length of schedule
        location = locations[0]

        # Get the corresponding total tablets and length of new schedule
        total_tablets = float(filtered_dosage_table.index[location[0]])
        length_of_new_schedule = float(filtered_dosage_table.columns[location[1]])

        # Build dosing schedule
        dosage_schedule = distribute_tablets(total_tablets, length_of_new_schedule, divisibility)

        eff_dose_change = ((new_dose - old_dose) / old_dose) * 100
        # Build dosing schedule
        dosage_schedule = distribute_tablets(total_tablets, length_of_new_schedule, divisibility)

        eff_dose_change = ((new_dose - old_dose) / old_dose) * 100

        # If the effective dosage change is zero, print a message and return
        if eff_dose_change == 0:
            output_message = "Ideal dosage schedule, no changes needed."
        else:
            adjustment_direction = "upwards" if eff_dose_change > 0 else "downwards"
            schedule_type = "weekly" if len(dosage_schedule) == 7 else "cyclical"

            # Generate the output message
            output_message = f"The dosage schedule was adjusted with {abs(eff_dose_change):.2f}% {adjustment_direction}.\n"
            output_message += "<table>"
            output_message += "<tr><th>Day</th><th>Dosage</th></tr>"
            for day, dosage in enumerate(dosage_schedule, start=1):
                output_message += f"<tr><td>Day {day}</td><td>{dosage}</td></tr>"
            output_message += "</table>"

        context = {
            'output_message': output_message,
            # ... Other relevant data
        }

        return render(request, 'result.html', context)

    return render(request, 'crcl.html')  # Render the input form initially
