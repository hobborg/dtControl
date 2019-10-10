if (X[1] <= 1.0) {
	if (X[0] <= 7.5) {
		if (X[3] <= 1.0) {
			return [1, 0, 0];
		}
		else {
			if (X[0] <= 6.5) {
				return [1, 0, 0];
			}
			else {
				return [1, 2, 0];
			}

		}

	}
	else {
		return [1, 2, 0];
	}

}
else {
	if (X[1] <= 7.0) {
		if (X[0] <= 19.5) {
			if (X[1] <= 5.0) {
				if (X[0] <= 12.5) {
					if (X[3] <= 5.0) {
						if (X[1] <= 3.0) {
							if (X[0] <= 8.5) {
								if (X[3] <= 3.0) {
									if (X[0] <= 7.5) {
										return [3, 0, 0];
									}
									else {
										if (X[3] <= 1.0) {
											return [3, 0, 0];
										}
										else {
											return [1, 3, 0];
										}

									}

								}
								else {
									return [1, 3, 0];
								}

							}
							else {
								if (X[3] <= 3.0) {
									if (X[0] <= 11.5) {
										return [1, 3, 0];
									}
									else {
										if (X[3] <= 1.0) {
											return [1, 3, 0];
										}
										else {
											return [1, 2, 3];
										}

									}

								}
								else {
									return [1, 2, 3];
								}

							}

						}
						else {
							if (X[3] <= 3.0) {
								return [3, 0, 0];
							}
							else {
								if (X[0] <= 9.5) {
									return [3, 0, 0];
								}
								else {
									return [1, 3, 0];
								}

							}

						}

					}
					else {
						if (X[0] <= 10.5) {
							if (X[3] <= 7.0) {
								if (X[1] <= 3.0) {
									return [1, 2, 3];
								}
								else {
									return [1, 3, 0];
								}

							}
							else {
								return [1, 2, 3];
							}

						}
						else {
							return [1, 2, 3];
						}

					}

				}
				else {
					if (X[1] <= 3.0) {
						return [1, 2, 3];
					}
					else {
						if (X[3] <= 5.0) {
							if (X[0] <= 15.5) {
								if (X[3] <= 1.0) {
									if (X[0] <= 13.5) {
										return [3, 0, 0];
									}
									else {
										return [1, 3, 0];
									}

								}
								else {
									return [1, 3, 0];
								}

							}
							else {
								if (X[3] <= 3.0) {
									if (X[0] <= 18.5) {
										return [1, 3, 0];
									}
									else {
										if (X[3] <= 1.0) {
											return [1, 3, 0];
										}
										else {
											return [1, 2, 3];
										}

									}

								}
								else {
									return [1, 2, 3];
								}

							}

						}
						else {
							return [1, 2, 3];
						}

					}

				}

			}
			else {
				if (X[3] <= 7.0) {
					if (X[3] <= 3.0) {
						return [3, 0, 0];
					}
					else {
						if (X[0] <= 11.5) {
							return [3, 0, 0];
						}
						else {
							if (X[3] <= 5.0) {
								if (X[0] <= 16.5) {
									return [3, 0, 0];
								}
								else {
									return [1, 3, 0];
								}

							}
							else {
								return [1, 3, 0];
							}

						}

					}

				}
				else {
					if (X[0] <= 12.5) {
						return [1, 3, 0];
					}
					else {
						return [1, 2, 3];
					}

				}

			}

		}
		else {
			if (X[1] <= 5.0) {
				return [1, 2, 3];
			}
			else {
				if (X[0] <= 28.5) {
					if (X[3] <= 5.0) {
						if (X[0] <= 24.5) {
							if (X[0] <= 20.5) {
								if (X[3] <= 1.0) {
									return [3, 0, 0];
								}
								else {
									return [1, 3, 0];
								}

							}
							else {
								return [1, 3, 0];
							}

						}
						else {
							if (X[3] <= 3.0) {
								if (X[0] <= 27.5) {
									return [1, 3, 0];
								}
								else {
									if (X[3] <= 1.0) {
										return [1, 3, 0];
									}
									else {
										return [1, 2, 3];
									}

								}

							}
							else {
								return [1, 2, 3];
							}

						}

					}
					else {
						return [1, 2, 3];
					}

				}
				else {
					return [1, 2, 3];
				}

			}

		}

	}
	else {
		if (X[0] <= 28.5) {
			if (X[3] <= 3.0) {
				return [3, 0, 0];
			}
			else {
				if (X[0] <= 25.5) {
					if (X[3] <= 5.0) {
						return [3, 0, 0];
					}
					else {
						if (X[0] <= 20.5) {
							if (X[3] <= 7.0) {
								return [3, 0, 0];
							}
							else {
								if (X[0] <= 13.5) {
									return [3, 0, 0];
								}
								else {
									return [1, 3, 0];
								}

							}

						}
						else {
							return [1, 3, 0];
						}

					}

				}
				else {
					return [1, 3, 0];
				}

			}

		}
		else {
			if (X[3] <= 1.0) {
				if (X[0] <= 29.5) {
					return [3, 0, 0];
				}
				else {
					return [1, 3, 0];
				}

			}
			else {
				return [1, 3, 0];
			}

		}

	}

}
