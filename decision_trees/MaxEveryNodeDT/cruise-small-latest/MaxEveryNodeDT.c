if (X[0] <= 28.5) {
	if (X[1] <= 1.0) {
		return 0;
	}
	else {
		return 3;
	}

}
else {
	if (X[0] <= 29.5) {
		if (X[3] <= 1.0) {
			if (X[1] <= 7.0) {
				return 1;
			}
			else {
				return 0;
			}

		}
		else {
			return 1;
		}

	}
	else {
		return 1;
	}

}
