import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from dotenv import load_dotenv

load_dotenv()

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Defined reusable paginate_questions function


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    paginated_questions = questions[start:end]

    return paginated_questions

# Defined reusable function for getting a random question from a list of questions


def get_random_question(questions):
    return questions[random.randint(0, len(questions) - 1)]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    # DONE!✅
    """
    CORS(app, resources={r"/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    # DONE!✅
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, PUT, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    DONE!✅
    """
    @app.route('/categories')
    def get_categories():
        try:
            categories = Category.query.all()
            formatted_categories = [category.format()
                                    for category in categories]
            return jsonify({
                'success': True,
                'categories': formatted_categories
            })
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    DONE!✅

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.

    TESTED!✅
    """
    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        paginated_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]

        if len(paginated_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(selection),
            'categories': formatted_categories,
            'current_category': None
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    DONE!✅

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.

    TESTED!✅
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(404)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    DONE!✅

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.

    TESTED!✅
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        searchTerm = body.get('searchTerm', None)

        if searchTerm:
            queriedSelection = Question.query.order_by(Question.id).filter(
                Question.question.ilike('%{}%'.format(searchTerm)))
            paginated_questions = paginate_questions(request, queriedSelection)

            if len(paginated_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': paginated_questions,
                'total_questions': len(queriedSelection.all()),
                'current_category': None
            })

        question = Question(question=new_question, answer=new_answer,
                            category=new_category, difficulty=new_difficulty)
        question.insert()

        return jsonify({
            'success': True,
            'created': question.id,
        })

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    DONE!✅

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.

    TESTED!✅
    """
    # !Refer to the create_question function above which contains the conditional logic for the search functionality

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    DONE!✅

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.

    TESTED!✅
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()
        paginated_questions = paginate_questions(request, selection)

        if len(paginated_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(selection),
            'current_category': category_id
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    DONE!✅

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.

    TESTED!✅
    """
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)
        quiz_category_id = quiz_category['id']

        if quiz_category_id == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter(
                Question.category == quiz_category_id).all()

        if len(questions) == 0:
            abort(404)

        question = get_random_question(questions)

        while question.id in previous_questions:
            question = get_random_question(questions)

        return jsonify({
            'success': True,
            'question': question.format(),
            'no_of_questions': len(questions)
        })

    """
    @TODO:

    DONE!✅
    
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app
