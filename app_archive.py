# from flask import Flask, request, send_file, jsonify
# from flask_cors import CORS
# import io
# from utils import generate_docx_from_data

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"])

# @app.route('/generate-doc', methods=['POST'])
# def generate_doc():
#     data = request.json
#     if not data:
#         return jsonify({"error": "No data provided"}), 400

#     file_name = data.get('fileName', 'follow_up')
#     form_data = {k: v for k, v in data.items() if k != 'fileName'}

#     try:
#         docx_io = generate_docx_from_data(form_data)
#         docx_io.seek(0)
#         return send_file(
#             docx_io,
#             mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#             download_name=f"{file_name}.docx",
#             as_attachment=True
#         )
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)
