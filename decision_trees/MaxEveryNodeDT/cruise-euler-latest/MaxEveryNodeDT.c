if (X[1] <= -9.0) {
	return 0;
}
else {
	if (X[1] <= 1.0) {
		if (X[0] <= 176.5) {
			return -2;
		}
		else {
			if (X[1] <= -3.0) {
				if (X[3] <= -3.5) {
					if (X[0] <= 198.5) {
						return -2;
					}
					else {
						if (X[1] <= -5.0) {
							return -2;
						}
						else {
							return 2;
						}

					}

				}
				else {
					return -2;
				}

			}
			else {
				if (X[3] <= -1.0) {
					return 2;
				}
				else {
					if (X[1] <= -1.0) {
						return -2;
					}
					else {
						return 2;
					}

				}

			}

		}

	}
	else {
		if (X[0] <= 112.5) {
			if (X[0] <= 102.5) {
				return -2;
			}
			else {
				if (X[1] <= 5.0) {
					if (X[3] <= 15.5) {
						if (X[0] <= 111.5) {
							return -2;
						}
						else {
							if (X[3] <= 13.5) {
								return -2;
							}
							else {
								if (X[3] <= 14.5) {
									return 2;
								}
								else {
									return -2;
								}

							}

						}

					}
					else {
						if (X[1] <= 3.0) {
							return -2;
						}
						else {
							return 2;
						}

					}

				}
				else {
					return -2;
				}

			}

		}
		else {
			if (X[3] <= 1.0) {
				if (X[0] <= 181.5) {
					return -2;
				}
				else {
					if (X[1] <= 15.0) {
						return 0;
					}
					else {
						return -2;
					}

				}

			}
			else {
				if (X[1] <= 13.0) {
					if (X[0] <= 144.5) {
						if (X[1] <= 11.0) {
							if (X[1] <= 3.0) {
								if (X[3] <= 10.5) {
									return 2;
								}
								else {
									if (X[3] <= 15.5) {
										if (X[0] <= 121.5) {
											return -2;
										}
										else {
											if (X[3] <= 11.5) {
												return -2;
											}
											else {
												if (X[0] <= 124.5) {
													if (X[3] <= 12.5) {
														return 2;
													}
													else {
														if (X[3] <= 13.5) {
															return -2;
														}
														else {
															return 2;
														}

													}

												}
												else {
													return 2;
												}

											}

										}

									}
									else {
										return 2;
									}

								}

							}
							else {
								if (X[3] <= 3.0) {
									return 0;
								}
								else {
									return 2;
								}

							}

						}
						else {
							return -2;
						}

					}
					else {
						return 2;
					}

				}
				else {
					if (X[0] <= 178.5) {
						if (X[0] <= 177.5) {
							return -2;
						}
						else {
							if (X[3] <= 19.0) {
								return -2;
							}
							else {
								return 0;
							}

						}

					}
					else {
						if (X[0] <= 186.5) {
							if (X[3] <= 9.0) {
								return -2;
							}
							else {
								if (X[3] <= 19.0) {
									return 0;
								}
								else {
									if (X[0] <= 185.5) {
										return 0;
									}
									else {
										if (X[1] <= 19.0) {
											return 2;
										}
										else {
											return 0;
										}

									}

								}

							}

						}
						else {
							if (X[1] <= 19.0) {
								if (X[3] <= 7.0) {
									return -2;
								}
								else {
									return 2;
								}

							}
							else {
								if (X[3] <= 9.0) {
									return -2;
								}
								else {
									return 0;
								}

							}

						}

					}

				}

			}

		}

	}

}
