def calculate_score(coin):

    try:

        volume = float(coin.get("volume", 0))
        change = float(coin.get("change", 0))

        score = 50

        if volume > 1000:
            score += 10

        if volume > 5000:
            score += 15

        if change > 0:
            score += change * 2

        if change > 10:
            score += 20

        if score > 100:
            score = 100

        return round(score, 2)

    except Exception as e:

        print("AI SCORE ERROR:", e)

        return 50