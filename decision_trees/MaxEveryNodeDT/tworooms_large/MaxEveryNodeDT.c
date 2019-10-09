if (X[1] <= 0.5) {
	if (X[3] <= 162.5) {
		return 2;
	}
	else {
		if (X[3] <= 163.5) {
			return 2;
		}
		else {
			return 1;
		}

	}

}
else {
	if (X[3] <= 161.5) {
		return 4;
	}
	else {
		return 3;
	}

}
