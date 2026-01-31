
import numpy as np
import pandas as pd
from datetime import date, timedelta

class SeasonalityEngine:
    def __init__(self, start_date=date(2024, 1, 1), days=366):
        self.start_date = start_date
        self.days = days
        self.date_range = [start_date + timedelta(days=x) for x in range(days)]
        self.df = pd.DataFrame({'date': self.date_range})
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['day_of_week'] = self.df['date'].dt.dayofweek # 0=Mon, 6=Sun
        self.df['month'] = self.df['date'].dt.month
        self.df['day'] = self.df['date'].dt.day

    def get_daily_multipliers(self):
        """
        Returns a DataFrame with a 'multiplier' column combining:
        1. Linear Trend (Growth)
        2. Weekly Seasonality (Weekend Spikes)
        3. Monthly Payday Effect
        4. Special Events (Black Friday, etc.)
        """
        # 1. Linear Trend (10% YoY growth)
        # y = mx + c. start at 1.0, end at 1.1
        slope = 0.10 / self.days
        self.df['trend'] = 1.0 + (self.df.index * slope)

        # 2. Weekly Seasonality
        # Mon: 0.9, Tue: 0.85, Wed: 0.9, Thu: 0.95, Fri: 1.0, Sat: 1.2, Sun: 1.3
        week_weights = {0: 0.9, 1: 0.85, 2: 0.9, 3: 0.95, 4: 1.0, 5: 1.2, 6: 1.3}
        self.df['weekly_seasonal'] = self.df['day_of_week'].map(week_weights)

        # 3. Monthly Payday Effect (Last 5 days of month)
        # Logic: If day > 25, multiplier = 1.15
        self.df['monthly_seasonal'] = np.where(self.df['day'] > 25, 1.15, 1.0)

        # 4. Special Events
        self.df['event_multiplier'] = 1.0
        
        # Summer Sale (July 15 - July 30)
        mask_summer = (self.df['month'] == 7) & (self.df['day'] >= 15) & (self.df['day'] <= 30)
        self.df.loc[mask_summer, 'event_multiplier'] = 1.5

        # Black Week (Nov 20 - Nov 27)
        mask_bf = (self.df['month'] == 11) & (self.df['day'] >= 20) & (self.df['day'] <= 27)
        self.df.loc[mask_bf, 'event_multiplier'] = 3.0

        # Christmas Rush (Dec 1 - Dec 15)
        mask_xmas = (self.df['month'] == 12) & (self.df['day'] <= 15)
        self.df.loc[mask_xmas, 'event_multiplier'] = 1.8
        
        # Christmas Slump (Dec 24 - Dec 26)
        mask_xmas_slump = (self.df['month'] == 12) & (self.df['day'] >= 24) & (self.df['day'] <= 26)
        self.df.loc[mask_xmas_slump, 'event_multiplier'] = 0.2

        # Combine all
        self.df['total_multiplier'] = (
            self.df['trend'] * 
            self.df['weekly_seasonal'] * 
            self.df['monthly_seasonal'] * 
            self.df['event_multiplier']
        )
        
        return self.df[['date', 'total_multiplier', 'event_multiplier']]

