from flask import Flask, request, abort

# instantiate Flask class
app = Flask(__name__)
# tell Flask what URL should trigger function
@app.route("/webhook", methods = ['POST'])
def webhook():
	if request.method == 'POST':
		print(request.json)
		return 'success', 200
	else:
		abort(400)


if __name__ == '__main__':
	app.run()
