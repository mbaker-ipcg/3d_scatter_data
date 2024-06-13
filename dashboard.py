from dash import Dash, html, dash_table, Input, Output, dcc
import pandas as pd
import sqlite3
import plotly.graph_objects as go


def generate_table_df(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


def generate_table_list(table_list):
    columns = ["Device ID", "X Position", "Y Position", "Z Position", "Device Type"]
    return dash_table.DataTable(
        id='data-table',
        columns=[{"name": col, "id": col} for col in columns],
        data=[{"Device ID": row[0], "X Position": row[1], "Y Position": row[2], "Z Position": row[3],
               "Device Type": row[4]} for row in table_list],
        page_size=10
    )


def generate_3d_plot(df):
    fig = go.Figure()
    # Create scatter trace for each device type
    for device_type in df['Device Type'].unique():
        df_type = df[df['Device Type'] == device_type]
        fig.add_trace(go.Scatter3d(
            x=df_type['X Position'],
            y=df_type['Y Position'],
            z=df_type['Z Position'],
            mode='markers',
            marker=dict(size=5),
            name=device_type
        ))
    # Set static axis ranges
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, 25]),
            yaxis=dict(range=[0, 25]),
            zaxis=dict(range=[0, 25]),
            aspectratio=dict(x=1, y=1, z=1),
        ),
        scene_camera=dict(
            center=dict(x=0, y=0, z=0),
            eye=dict(x=.2, y=.2, z=.2)
        )
    )

    return fig


def connectdb():
    connection = sqlite3.connect('database.sqlite')
    try:
        cursor = connection.cursor()
        # print("Database Opened")
        return connection, cursor
    except sqlite3.Error as e:
        print(e)
        exit()


def get_start_time():
    connection, cursor = connectdb()
    cursor.execute("SELECT MIN(time) FROM position")
    start_time = cursor.fetchone()[0]
    connection.close()
    return start_time


def get_end_time():
    connection, cursor = connectdb()
    cursor.execute("SELECT MAX(time) FROM position")
    end_time = cursor.fetchone()[0]
    connection.close()
    return end_time


def get_data_df(time):
    connection, cursor = connectdb()
    cursor.execute("SELECT * FROM position WHERE time = ?", (time,))
    devices = cursor.fetchall()
    dev_dict = {
        "dev_id": [],
        "x_pos": [],
        "y_pos": [],
        "z_pos": [],
        "dev_type": []
    }
    for device in devices:
        dev_dict["dev_id"].append(device[0])
        dev_dict["x_pos"].append(device[1])
        dev_dict["y_pos"].append(device[2])
        dev_dict["z_pos"].append(device[3])
        dev_dict["dev_type"].append(device[4])
    table = pd.DataFrame(dev_dict)
    connection.close()
    return table


def get_data_list(time):
    connection, cursor = connectdb()
    cursor.execute("SELECT device_id, x_pos, y_pos, z_pos, device_type FROM position WHERE time = ?", (time,))
    devices = cursor.fetchall()
    connection.close()
    print(time)
    print(devices)
    return devices


def increment_timestamp(time):
    date, time = time.split()
    hour, minute, second = time.split(':')
    second = int(second) + 1
    if second > 59:
        second = second - 60
        minute = int(minute) + 1
        if minute > 59:
            minute = minute - 60
            hour = int(hour) + 1
            if hour > 23:
                hour = hour - 24
                # TODO increment day if hour > 24
    second = str(second).zfill(2)
    minute = str(minute).zfill(2)
    hour = str(hour).zfill(2)
    time = f"{date} {hour}:{minute}:{second}"
    if time == get_end_time():
        return get_start_time()
    # time = date + " " + str(hour) + ":" + str(minute) + ":" + str(second)
    return time


app = Dash()

app.layout = html.Div([
    dcc.Graph(id='3d-plot'),
    html.Div(id='table-container'),
    html.H4(id='time', children=get_start_time()),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])


@app.callback(
    Output('table-container', 'children'),
    Output('3d-plot', 'figure'),
    Output('time', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('time', 'children')
)
def update_output(n_intervals, current_time):
    new_time = increment_timestamp(current_time)
    new_table = get_data_list(new_time)
    df = pd.DataFrame(new_table, columns=['Device ID', 'X Position', 'Y Position', 'Z Position', 'Device Type'])
    table = generate_table_list(new_table)
    figure = generate_3d_plot(df)
    return table, figure, new_time


if __name__ == '__main__':
    app.run_server(debug=True)
