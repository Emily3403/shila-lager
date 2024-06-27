beverage_categories = {
    "Wicküler": ("#ffdb3e", ["B1278"]),
    "Pilsator": ("#fbc72e", ["B1183"]),
    "Jever": ("#f6b31f", ["B1165"]),
    "Berliner Kindl": ("#f09f12", ["B1040"]),
    "Andechs": ("#e98b07", ["B0995"]),

    "Anderes Bier": ("#d77900", ["B1345", "B1357", "B1047", "B0996", "B1035", "B1053", "B1245", "B1225", "B0991"]),
    "Limo": ("#cb7eff", ["E3122", "E3125", "E3126", "E3127", "E3128", "E3130", "E3132", "E3224", "E3347", "E3351", "E3354", "E3416", "E3417", "E3418", "E3419"]),
    "Mate": ("#ffe247", ["E3433", "E3438", "E3445", "E3450"]),
    "Spezi": ("#8b4513", ["E3446"]),
    "Soli": ("forestgreen", ["E3451", "E3456"]),
    "Wasser": ("#1e90ff", ["M4135", "M4195"]),
    "Sekt": ("#f0e6c1", ["O7040", "O7060", "O7185"]),
    "Wein": ("#9f0f89", ["W8010", "W8012", "W8017", "W8019", "W8021", "W8025", "W8028", "W8033"]),
}

meta_categories = {
    "Billiges Bier": ("#e39119", ["Pilsator", "Wicküler"]),
    "Teures Bier": ("#c66700", ["Andechs", "Berliner Kindl", "Jever"]),
    "Anderes Bier": ("#a4590a", ["Anderes Bier"]),
    "Softdrinks": ("#7f29b9", ["Mate", "Soli", "Spezi", "Limo"]),
    "Sekt": ("#e5ce76", ["Sekt"]),
    "Wein": ("#650a59", ["Wein"]),
    "Wasser": ("#0073e4", ["Wasser"]),
}

digest_categories = {
    "Bier": ["B1278", "B1183", "B1165", "B1040", "B0995", "B1345", "B1357", "B1047", "B0996", "B1035", "B1053", "B1245", "B1225", "B0991", "B1092"],
    "Softdrinks": ["E3433", "E3438", "E3445", "E3450", "E3446", "E3451", "E3456", "E3122", "E3125", "E3126", "E3127", "E3128", "E3130", "E3132", "E3347", "E3351", "E3354", "E3416", "E3417", "E3418", "E3419"],
    "Wasser / Apfelschorle": ["E3224", "M4135", "M4195"],
    "Sekt / Wein": ["O7040", "O7060", "O7185", "W8010", "W8012", "W8017", "W8019", "W8021", "W8025", "W8028", "W8033"],
}

# In digestions, this is which beverages should be actually analyzed as the same
collapse_categories = {
    "O7060": ["O7040", "O7060", "O7185"],
    "W8021": ["W8010", "W8012", "W8017", "W8019", "W8021", "W8025", "W8028", "W8033"],
}

soli_ids = {"E3451", "E3456"}
