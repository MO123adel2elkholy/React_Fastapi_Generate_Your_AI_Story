import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import LoadingStatus from "./LoadingStatus.jsx";
import StoryGame from "./StoryGame.jsx";

// API base URL for backend calls.
// This is configured as a proxy path to avoid hardcoding the backend host.
const API_BASE_URL = "/api";

// StoryLoader component:
// Loads a previously generated story by ID and renders the story gameplay UI.
// It handles loading, errors, and the transition to the main story experience.
function StoryLoader() {
    // Get the story id from the route params, for example: /story/42
    const { id } = useParams();

    // React Router navigation hook used to redirect back to home when needed.
    const navigate = useNavigate();

    // Store the loaded story data returned by the backend.
    const [story, setStory] = useState(null);

    // Tracks whether the story is currently being fetched.
    const [loading, setLoading] = useState(true);

    // Stores any fetch or validation error for user feedback.
    const [error, setError] = useState(null);

    // Fetch the story whenever the route param `id` changes.
    useEffect(() => {
        loadStory(id);
    }, [id]);

    // loadStory:
    // Makes a GET request to the backend to fetch the full story tree.
    // On success, stores the story in state.
    // On failure, sets an appropriate user-friendly error message.
    const loadStory = async (storyId) => {
        setLoading(true);
        setError(null);

        try {
            const response = await axios.get(
                `${API_BASE_URL}/stories/${storyId}/complete`
            );

            setStory(response.data);
        } catch (err) {
            // If the backend returns 404, the story does not exist.
            if (err.response?.status === 404) {
                setError("Story is not found.");
            } else {
                setError("Failed to load story");
            }
        } finally {
            setLoading(false);
        }
    };

    // Go back to the main page to create a new story.
    const createNewStory = () => {
        navigate("/");
    };

    // While the story is still loading, show a loading indicator.
    if (loading) {
        return <LoadingStatus theme={"story"} />;
    }

    // If a fetch error occurred, show an error panel with a button to restart.
    if (error) {
        return (
            <div className="story-loader">
                <div className="error-message">
                    <h2>Story Not Found</h2>
                    <p>{error}</p>
                    <button onClick={createNewStory}>Go to Story Generator</button>
                </div>
            </div>
        );
    }

    // Once the story is loaded, show the gameplay component.
    if (story) {
        return (
            <div className="story-loader">
                <StoryGame story={story} onNewStory={createNewStory} />
            </div>
        );
    }

    // Fallback in case there is no story and no error.
    return null;
}

export default StoryLoader;