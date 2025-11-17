"""
Nifty 15m Pro Strategy v7-Lite

Converted from Pine Script to Python
Uses Supertrend indicator with ADX filter for trend confirmation

Entry Rules:
- Long: Supertrend bearish + ADX > threshold
- Short: Supertrend bullish + ADX > threshold

Exit Rules:
- Fixed SL and TP based on ATR
- SL = 5000 + 1.1 * ATR(14)
- TP = 5000 + 2.1 * ATR(14)
"""

import pandas as pd
import numpy as np
from ..base_strategy import BaseStrategy


class Nifty15mProStrategy(BaseStrategy):
    """
    Nifty 15-minute Pro Strategy using Supertrend and ADX
    
    Best for: 15-minute timeframe on NIFTY
    Capital Required: ₹100,000 (margin: 75%)
    """
    
    def __init__(self, 
                 supertrend_factor=3.0,
                 atr_period=10,
                 adx_period=14,
                 adx_threshold=30,
                 sl_base=5000,
                 tp_base=5000,
                 sl_atr_multiplier=1.1,
                 tp_atr_multiplier=2.1):
        """
        Initialize Nifty 15m Pro Strategy
        
        Args:
            supertrend_factor: Multiplier for ATR in Supertrend calculation
            atr_period: Period for ATR calculation in Supertrend
            adx_period: Period for ADX calculation
            adx_threshold: Minimum ADX value for trade entry
            sl_base: Base stop loss in rupees
            tp_base: Base target profit in rupees
            sl_atr_multiplier: ATR multiplier for stop loss
            tp_atr_multiplier: ATR multiplier for take profit
        """
        super().__init__("Nifty 15m Pro Strategy")
        self.supertrend_factor = supertrend_factor
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.sl_base = sl_base
        self.tp_base = tp_base
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
    
    def calculate_supertrend(self, df, period, multiplier):
        """
        Calculate Supertrend indicator
        
        Returns:
            tuple: (supertrend_values, direction)
                  direction: 1 for uptrend (bullish), -1 for downtrend (bearish)
        """
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        
        # Calculate basic bands
        hl_avg = (df['high'] + df['low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize supertrend
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=float)
        
        supertrend.iloc[0] = upper_band.iloc[0]
        direction.iloc[0] = 1
        
        for i in range(1, len(df)):
            # Update bands based on previous values
            if df['close'].iloc[i] > supertrend.iloc[i-1]:
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < supertrend.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]
            
            # Set supertrend value
            if direction.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
                if supertrend.iloc[i] < supertrend.iloc[i-1]:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
                if supertrend.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
        
        return supertrend, direction
    
    def calculate_adx(self, df, period):
        """
        Calculate ADX (Average Directional Index)
        
        Returns:
            tuple: (plus_di, minus_di, adx)
        """
        # Calculate directional movement
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = pd.Series(np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0), index=df.index)
        minus_dm = pd.Series(np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0), index=df.index)
        
        # Calculate ATR for ADX
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        
        # Calculate Directional Indicators
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return plus_di, minus_di, adx
    
    def calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        
        return atr
    
    def generate_signals(self, df):
        """
        Generate trading signals based on Supertrend and ADX
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            DataFrame with additional columns for signals
        """
        df = df.copy()
        
        # Calculate Supertrend
        supertrend, direction = self.calculate_supertrend(
            df, self.atr_period, self.supertrend_factor
        )
        df['supertrend'] = supertrend
        df['supertrend_direction'] = direction
        
        # Calculate ADX
        plus_di, minus_di, adx = self.calculate_adx(df, self.adx_period)
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        df['adx'] = adx
        
        # Calculate ATR for SL/TP
        atr_14 = self.calculate_atr(df, 14)
        df['atr_14'] = atr_14
        
        # Determine bull/bear conditions
        df['bull'] = (df['supertrend_direction'] == 1).astype(int)
        df['bear'] = (df['supertrend_direction'] == -1).astype(int)
        
        # ADX filter
        df['adx_ok'] = (df['adx'] > self.adx_threshold).astype(int)
        
        # Entry signals
        # In Pine Script: shortEntry = bull and adxOk (inverted logic for short)
        # longEntry = bear and adxOk (inverted logic for long)
        df['short_entry'] = (df['bull'] == 1) & (df['adx_ok'] == 1)
        df['long_entry'] = (df['bear'] == 1) & (df['adx_ok'] == 1)
        
        # Calculate SL and TP
        df['sl_points'] = self.sl_base + (self.sl_atr_multiplier * df['atr_14'])
        df['tp_points'] = self.tp_base + (self.tp_atr_multiplier * df['atr_14'])
        
        # Generate signal column (1 for long, -1 for short, 0 for no signal)
        df['signal'] = 0
        df.loc[df['long_entry'], 'signal'] = 1
        df.loc[df['short_entry'], 'signal'] = -1
        
        return df
    
    def get_parameters(self):
        """Return strategy parameters"""
        return {
            'supertrend_factor': self.supertrend_factor,
            'atr_period': self.atr_period,
            'adx_period': self.adx_period,
            'adx_threshold': self.adx_threshold,
            'sl_base': self.sl_base,
            'tp_base': self.tp_base,
            'sl_atr_multiplier': self.sl_atr_multiplier,
            'tp_atr_multiplier': self.tp_atr_multiplier
        }
    
    def calculate_score(self, df):
        """
        Calculate strategy score based on signal strength and conditions
        
        Returns:
            float: Score between 0-100
        """
        df_with_signals = self.generate_signals(df)
        
        # Count valid signals
        total_signals = (df_with_signals['signal'] != 0).sum()
        
        if total_signals == 0:
            return 0.0
        
        # Calculate signal quality
        strong_adx = (df_with_signals['adx'] > self.adx_threshold * 1.5).sum()
        adx_quality = strong_adx / len(df_with_signals) * 100
        
        # Calculate trend strength
        trend_changes = (df_with_signals['supertrend_direction'].diff() != 0).sum()
        trend_stability = max(0, 100 - (trend_changes / len(df_with_signals) * 100))
        
        # Signal frequency score
        signal_frequency = min(100, (total_signals / len(df_with_signals)) * 1000)
        
        # Composite score
        score = (adx_quality * 0.4 + trend_stability * 0.3 + signal_frequency * 0.3)
        
        return min(100.0, max(0.0, score))
