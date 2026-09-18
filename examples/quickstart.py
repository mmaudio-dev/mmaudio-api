        """Minimal MMAudio example: create one prediction and print the output URL(s)."""
        import mmaudio_api

        output = mmaudio_api.run({
    "video": "https://example.com/input.png",
    "prompt": "galloping"
})
        print(output)
