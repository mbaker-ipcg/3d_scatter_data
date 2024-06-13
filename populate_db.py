import csv

filename = 'data/Rounded_Device_Movement_Data.csv'

with open(filename, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    data = []
    header = True
    for row in reader:
        if header:
            header = False
        else:
            data.append(row)
    insert_records = "INSERT INTO position (device_id, x_pos, y_pos, z_pos, device_type, time) VALUES (?, ?, ?, ?, ?, ?);"
    cursor.executemany(insert_records, data)

connection.commit()
connection.close()
