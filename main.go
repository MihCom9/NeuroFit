package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/google/generative-ai-go/genai"
	"github.com/joho/godotenv"
	"google.golang.org/api/option"
)

type ChatRequest struct {
	Message string `json:"message"`
}

type ChatResponse struct {
	Reply string `json:"reply"`
}

var model *genai.GenerativeModel
var ctx context.Context

func main() {
	// Load environment variables
	godotenv.Load(".env")
	apiKey := os.Getenv("API_KEY")
	if apiKey == "" {
		log.Fatal("API_KEY not found in .env file")
	}

	ctx = context.Background()
	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		log.Fatal("Failed to create genai client:", err)
	}
	defer client.Close()

	model = client.GenerativeModel("gemini-2.0-flash")

	// Serve static files
	http.Handle("/", http.FileServer(http.Dir("./public")))

	// Chat endpoint
	http.HandleFunc("/chat", chatHandler)

	log.Println("Server started at http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}

func chatHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("Received a request at /chat")

	var req ChatRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		log.Println("Error decoding JSON:", err)
		respondWithJSON(w, http.StatusBadRequest, ChatResponse{Reply: "Invalid request format."})
		return
	}
	log.Println("User message:", req.Message)
	resp, err := model.GenerateContent(ctx, genai.Text(req.Message))
	if err != nil || resp == nil || len(resp.Candidates) == 0 {
		log.Println("Error generating content:", err)
		respondWithJSON(w, http.StatusInternalServerError, ChatResponse{Reply: "AI error, try again later."})
		return
	}

	reply := ""
	if parts := resp.Candidates[0].Content.Parts; len(parts) > 0 {
		if text, ok := parts[0].(genai.Text); ok {
			reply = string(text)
		}
	}

	log.Println("AI reply:", reply)
	respondWithJSON(w, http.StatusOK, ChatResponse{Reply: reply})
}

func respondWithJSON(w http.ResponseWriter, status int, payload ChatResponse) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}
