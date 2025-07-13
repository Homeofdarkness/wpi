from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, InnerPoliticsStats
from utils.input_parsers import InputParser

text1 = InputParser.parse_data_from_str()
text2 = InputParser.parse_data_from_str()
Economy = EconomyStats.from_stats_text(text1 + '\n' + text2)
