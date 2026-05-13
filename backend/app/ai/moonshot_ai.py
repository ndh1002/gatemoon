def calculate_score(coin):
    score = 0

    volume = float(coin.get("volume", 0))
    change = float(coin.get("change", 0))

    if volume > 1000000:
        score += 25

    if change > 5:
        score += 20

    if change > 15:
        score += 25

    if volume > 5000000:
        score += 20

    volatility = abs(change)

    if volatility > 20:
        score += 10

    return min(score, 100)