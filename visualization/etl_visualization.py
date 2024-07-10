from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

etl_path = os.path.join(BASE_DIR, "../data/etl_zoo.csv")

df = pd.read_csv(etl_path)

species_count = df['species'].value_counts()
health_status_count = df['health_status'].value_counts()

fig, axes = plt.subplots(3, 1, figsize=(10, 18))


sns.histplot(data=df, x='species', hue='health_status', multiple='dodge', shrink=0.8, ax=axes[0])
axes[0].set_title('Relationship between Species and Health Status')
axes[0].set_xlabel('Species')
axes[0].set_ylabel('Count')

axes[1].pie(species_count, labels=species_count.index, autopct='%1.1f%%', startangle=90)
axes[1].set_title('Species Distribution')


axes[2].pie(health_status_count, labels=health_status_count.index, autopct='%1.1f%%', startangle=90)
axes[2].set_title('Health Status Distribution')


plt.tight_layout()
plt.savefig('combined_plots.png')
plt.show()