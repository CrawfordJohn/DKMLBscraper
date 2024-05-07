import pandas as pd

def equation(y, c1, c2):
    return c1 ** y + c2 ** y - 1


def solve_equation(c1, c2, tolerance=1e-6, max_iterations=1000):
    y_lower = 0
    y_upper = 2

    # Check if the initial guesses are valid
    if equation(y_lower, c1, c2) * equation(y_upper, c1, c2) > 0:
        return None  # No solution within the given range

    # Bisection method
    for _ in range(max_iterations):
        y_mid = (y_lower + y_upper) / 2
        if abs(equation(y_mid, c1, c2)) < tolerance:
            return y_mid
        elif equation(y_lower, c1, c2) * equation(y_mid, c1, c2) < 0:
            y_upper = y_mid
        else:
            y_lower = y_mid

    return None  # No solution found within max_iterations
def devig(probs):
    k = solve_equation(probs[0], probs[1])
    return (probs[0]**k, probs[1]**k)

def true_odds(df):
    hold_list = []
    over_odds = []
    under_odds = []
    over_true_prob = []
    under_true_prob = []
    for i, row in df.iterrows():
        if (type(row['over_odds']) == str) & (type(row['under_odds']) == str):
            if row['over_odds'][0] == '+':
                over_prob = 100 / (100 +int(row['over_odds'][1:]) )
            else:
                over_prob = int(row['over_odds'][1:]) / (100 + int(row['over_odds'][1:]))
            if row['under_odds'][0] == '+':
                under_prob = 100 / (100 + int(row['under_odds'][1:]))
            else:
                under_prob = int(row['under_odds'][1:]) / (100 + int(row['under_odds'][1:]))
            hold = over_prob + under_prob - 1
            hold_list.append(hold)
            over_odds.append(1/over_prob)
            under_odds.append(1/under_prob)
            true_over_prob, true_under_prob = devig([over_prob, under_prob])
            over_true_prob.append(true_over_prob)
            under_true_prob.append(true_under_prob)
        else:
            hold_list.append(None)
            over_odds.append(None)
            under_odds.append(None)
            over_true_prob.append(None)
            under_true_prob.append(None)

    df['hold'] = hold_list
    df['over_odds'] = over_odds
    df['under_odds'] = under_odds
    df['over_true_prob'] = over_true_prob
    df['under_true_prob'] = under_true_prob
    df[['under_odds', 'over_odds', 'hold', 'over_true_prob', 'under_true_prob']] = round(df[['under_odds', 'over_odds', 'hold', 'over_true_prob', 'under_true_prob']], 3)
    return df

closer = pd.read_csv('closer.csv')

true_odds(closer).to_csv('closer.csv')