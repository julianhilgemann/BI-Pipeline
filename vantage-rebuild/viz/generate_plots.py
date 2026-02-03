import sys
import os

# Add data_generation/src to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data_generation/src')))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from seasonality import SeasonalityEngine
from generators import ProductGenerator
from datetime import date

def setup_style():
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12

def plot_seasonality(output_dir):
    print("Generating Seasonality Plot...")
    engine = SeasonalityEngine(start_date=date(2024, 1, 1), days=365)
    df = engine.get_daily_multipliers()
    
    plt.figure(figsize=(12, 6))
    
    # Plot Total Multiplier
    plt.plot(df['date'], df['total_multiplier'], label='Total Lambda Multiplier', color='#2c3e50', linewidth=1.5)
    
    # Highlight specific components
    # Payday effects (end of month spikes)
    # We can annotate or just let the visual speak. 
    # Use fill_between for events
    
    # Black Week
    mask_bf = (df['date'].dt.month == 11) & (df['date'].dt.day >= 20) & (df['date'].dt.day <= 27)
    plt.fill_between(df['date'], 0, df['total_multiplier'], where=mask_bf, color='#e74c3c', alpha=0.3, label='Black Week')
    
    # Summer Sale
    mask_summer = (df['date'].dt.month == 7) & (df['date'].dt.day >= 15) & (df['date'].dt.day <= 30)
    plt.fill_between(df['date'], 0, df['total_multiplier'], where=mask_summer, color='#f1c40f', alpha=0.3, label='Summer Sale')
    
    plt.title('Non-Homogeneous Poisson Process: Seasonality Driver ($\\lambda_t$)', fontweight='bold')
    plt.ylabel('Demand Multiplier (Baseline = 1.0)')
    plt.xlabel('Date')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'seasonality_curve.png'), dpi=150)
    plt.close()

def plot_distributions(output_dir):
    print("Generating Product Distributions...")
    gen = ProductGenerator(num_products=1000) # Generate more for smoother plots
    df = gen.generate()
    
    # 1. Price Distribution (Log-Normal)
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='avg_price_eur', hue='category', kde=True, element="step", palette='viridis')
    plt.title('Product Price Distribution (Log-Normal Mix)', fontweight='bold')
    plt.xlabel('Price (EUR)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_distribution.png'), dpi=150)
    plt.close()
    
    # 2. Pareto Popularity
    plt.figure(figsize=(10, 6))
    # Sort by popularity
    sorted_pop = df.sort_values('popularity_score', ascending=False).reset_index(drop=True)
    # Plot Lorenz Curve-style or just the decay
    plt.plot(sorted_pop.index, sorted_pop['popularity_score'], color='#e74c3c', linewidth=2)
    plt.fill_between(sorted_pop.index, 0, sorted_pop['popularity_score'], color='#e74c3c', alpha=0.1)
    
    plt.title('Product Affinity (Pareto Distribution)', fontweight='bold')
    plt.xlabel('Product Rank')
    plt.ylabel('Selection Probability Score')
    # Annotate "The Long Tail"
    plt.annotate('The Independent Head\n(Bestsellers)', xy=(10, sorted_pop['popularity_score'].iloc[10]), 
                 xytext=(100, sorted_pop['popularity_score'].iloc[10]*1.5),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'pareto_affinity.png'), dpi=150)
    plt.close()

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True) # visual artifacts go into viz/
    
    setup_style()
    plot_seasonality(output_dir)
    plot_distributions(output_dir)
    print(f"Plots saved to {output_dir}")

if __name__ == "__main__":
    main()
