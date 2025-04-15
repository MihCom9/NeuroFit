package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"

	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/option"
)

func main() {
	err := godotenv.Load(".env")
	if err != nil {
		log.Fatal("Error loading .env file", err)
	}
	// Access your API key as an environment variable (see "Set up your API key" above)
	apiKey := os.Getenv("API_KEY")
	ctx := context.Background()
	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {

		log.Fatal(err)

	}
	defer client.Close()
	reader := bufio.NewReader(os.Stdin)
	model := client.GenerativeModel("gemini-2.0-flash")

	for {

		fmt.Print("You:")
		input, _ := reader.ReadString('\n')

		// For text-only input, use the gemini-pro model

		resp, err := model.GenerateContent(ctx, genai.Text(input))

		if resp != nil {
			candidats := resp.Candidates
			if candidats != nil {
				for _, candidats := range candidats {
					content := candidats.Content
					if content != nil {
						text := content.Parts[0]
						log.Println("Candidat content text:", text)
					}
				}

			} else {
				log.Println("Candidat slice is nil ")
			}
		} else {
			log.Println("Response is nil")
		}

		if err != nil {

			log.Fatal(err)
		}
	}

}
