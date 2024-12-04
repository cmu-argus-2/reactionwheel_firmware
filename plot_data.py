import plotly
import pandas as pd


# TODO: Write a function that uses's scipy's RANSAC function to remove outliers
# before solving for a linear line of best fit via least squares.


# TODO: Write a function that takes the processed measurements and generates a
# plotly scatter plot. This function should receive the processed data in the
# form of a pandas dataframe and return a plotly figure object. It is expected
# ahead of time that only two columns will be present in the dataframe: one for
# x and one for y, with column names for each.
def plot_measurements(measurements_df: pd.DataFrame,
                      x_col_name: str,
                      y_col_name: str) -> plotly.graph_objs.Figure:
    # Create a scatter plot of the measurements
    fig = plotly.graph_objs.Figure()
    fig.add_trace(plotly.graph_objs.Scatter(x=measurements_df[y_col_name], y=measurements_df[y_col_name], mode='markers'))
    fig.update_layout(title='Measurements',
                      xaxis_title=x_col_name,
                      yaxis_title=y_col_name)
    return fig