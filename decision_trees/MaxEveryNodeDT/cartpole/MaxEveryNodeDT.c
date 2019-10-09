if (X[1] <= -0.85) {
	return 63;
}
else {
	if (X[1] <= -0.05) {
		if (X[0] <= 3.72) {
			return 77;
		}
		else {
			return 12;
		}

	}
	else {
		if (X[0] <= 2.6) {
			if (X[1] <= 0.05) {
				return 80;
			}
			else {
				return 25;
			}

		}
		else {
			return 4;
		}

	}

}
