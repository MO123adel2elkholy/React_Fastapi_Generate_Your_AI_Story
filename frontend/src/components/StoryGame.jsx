import { useState, useEffect } from "react";

// StoryGame component:
// Displays the current story node and allows the user to move through
// the branching narrative by selecting available options.
// Receives:
// - story: the full generated story payload from the backend
// - onNewStory: callback to go back and generate a different story
function StoryGame({ story, onNewStory }) {
    // currentNodeId tracks the active node currently being displayed.
    // This value changes as the user clicks one of the options.
    const [currentNodeId, setCurrentNodeId] = useState(null);

    // currentNode stores the currently selected node object from the story tree.
    const [currentNode, setCurrentNode] = useState(null);

    // options stores the list of selectable choices for the current node.
    const [options, setOptions] = useState([]);

    // isEnding indicates whether the current node is an ending node.
    const [isEnding, setIsEnding] = useState(false);

    // isWinningEnding indicates whether the current ending is a winning ending.
    const [isWinningEnding, setIsWinningEnding] = useState(false);

    // When the story loads or changes, set the initial current node to the root node.
    useEffect(() => {
        if (story && story.root_node) {
            const rootNodeId = story.root_node.id;
            setCurrentNodeId(rootNodeId);
        }
    }, [story]);

    // When the currentNodeId or story changes, look up the node from `story.all_nodes`
    // and update the UI state for the content, ending flags, and available choices.
    useEffect(() => {
        if (currentNodeId && story && story.all_nodes) {
            const node = story.all_nodes[currentNodeId];

            setCurrentNode(node);
            setIsEnding(node.is_ending);
            setIsWinningEnding(node.is_winning_ending);

            // Only non-ending nodes should show interactive options.
            if (!node.is_ending && node.options && node.options.length > 0) {
                setOptions(node.options);
            } else {
                setOptions([]);
            }
        }
    }, [currentNodeId, story]);

    // chooseOption:
    // Moves the story forward by selecting a branch option.
    // The option's `node_id` is the next node to display.
    const chooseOption = (optionId) => {
        setCurrentNodeId(optionId);
    };

    // restartStory:
    // Resets the story to the root node so the user can replay the adventure.
    const restartStory = () => {
        if (story && story.root_node) {
            setCurrentNodeId(story.root_node.id);
        }
    };

    return (
        <div className="story-game">
            {/* Story title displayed at the top */}
            <header className="story-header">
                <h2>{story.title}</h2>
            </header>

            <div className="story-content">
                {/* Render the current story node only if it exists */}
                {currentNode && (
                    <div className="story-node">
                        <p>{currentNode.content}</p>

                        {/* If this node is an ending, show a final ending panel */}
                        {isEnding ? (
                            <div className="story-ending">
                                <h3>{isWinningEnding ? "Congratulations" : "The End"}</h3>
                                {isWinningEnding
                                    ? "You reached a winning ending"
                                    : "Your adventure has ended."}
                            </div>
                        ) : (
                            // Otherwise, render the available choices for this node.
                            <div className="story-options">
                                <h3>What will you do?</h3>
                                <div className="options-list">
                                    {options.map((option, index) => {
                                        return (
                                            <button
                                                key={index}
                                                onClick={() => chooseOption(option.node_id)}
                                                className="option-btn"
                                            >
                                                {option.text}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="story-controls">
                {/* Restart button resets to the beginning of the story */}
                <button onClick={restartStory} className="reset-btn">
                    Restart Story
                </button>
            </div>

            {/* Optional callback to generate a new story */}
            {onNewStory && (
                <button onClick={onNewStory} className="new-story-btn">
                    New Story
                </button>
            )}
        </div>
    );
}

export default StoryGame;