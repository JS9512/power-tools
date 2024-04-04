from pyrlottie import run, convMultLottie, LottieFile, FileMap
import sys

# convMultLottie
print(
	run(
		convMultLottie(
			[
				FileMap(LottieFile(sys.argv[1]), {f"anime.gif"})

			]
		)
	)
)