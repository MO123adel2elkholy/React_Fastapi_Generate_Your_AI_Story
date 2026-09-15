
"""Story-generation prompt templates.

This module defines the prompt text used to instruct the language model to
generate a branching choose-your-own-adventure story in JSON format.

The main prompt, STORY_PROMPT, tells the model to produce:
- a story title
- a root node with 2-3 choices
- nested narrative branches
- multiple endings, including at least one winning ending
- a consistent JSON structure with no extra text outside the output

The json_structure constant acts as a blueprint for the expected story tree,
showing how each node contains story content, ending flags, and nested options.

This file serves as the contract between the AI model output and the backend
parser that converts the JSON into database records and story nodes.
"""







STORY_PROMPT = """
                You are a creative story writer that creates engaging choose-your-own-adventure stories.
                Generate a complete branching story with multiple paths and endings in the JSON format I'll specify.

                The story should have:
                1. A compelling title
                2. A starting situation (root node) with 2-3 options
                3. Each option should lead to another node with its own options
                4. Some paths should lead to endings (both winning and losing)
                5. At least one path should lead to a winning ending

                Story structure requirements:
                - Each node should have 2-3 options except for ending nodes
                - The story should be 3-4 levels deep (including root node)
                - Add variety in the path lengths (some end earlier, some later)
                - Make sure there's at least one winning path

                Output your story in this exact JSON structure:
                {format_instructions}

                Don't simplify or omit any part of the story structure. 
                Don't add any text outside of the JSON structure.
                """

json_structure = """
        {
            "title": "Story Title",
            "rootNode": {
                "content": "The starting situation of the story",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                    {
                        "text": "Option 1 text",
                        "nextNode": {
                            "content": "What happens for option 1",
                            "isEnding": false,
                            "isWinningEnding": false,
                            "options": [
                                // More nested options
                            ]
                        }
                    },
                    // More options for root node
                ]
            }
        }
        """
