"""Optional Matplotlib chart builders used by future report views."""
from matplotlib.figure import Figure


def expense_pie_chart(rows):
    figure = Figure(figsize=(5, 3), facecolor="#1E293B")
    axis = figure.add_subplot(111)
    labels = [row["category"] for row in rows]
    values = [row["total"] for row in rows]
    if values:
        axis.pie(values, labels=labels, autopct="%1.0f%%", textprops={"color": "white"})
    else:
        axis.text(0.5, 0.5, "No expense data", ha="center", color="white")
    axis.set_facecolor("#1E293B")
    return figure
