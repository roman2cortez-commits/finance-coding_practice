# Pandas practice
import pandas as pd

data = {"item": ["rent", "food", "gas"], "cost": [1200, 300, 80]}
df = pd.DataFrame(data)
print(df)
print("Total:", df["cost"].sum())
