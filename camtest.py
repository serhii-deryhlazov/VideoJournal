import cv2

def test_webcam():
    print("Testing webcam access...")
    
    # Try webcam indices 0 to 4
    for index in range(5):
        print(f"\nTrying webcam index {index}...")
        cap = cv2.VideoCapture(index)
        
        # Check if webcam opened successfully
        if cap.isOpened():
            print(f"Webcam opened successfully (index {index})")
            print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            print("Press 'q' to quit the webcam preview.")
            print("Check the preview to identify the camera (built-in or iPhone).")
            
            while True:
                ret, frame = cap.read()
                print("Frame captured:", ret)
                
                if ret:
                    # Display the frame
                    cv2.imshow(f"Webcam Test (Index {index})", frame)
                else:
                    print("Error: Could not capture frame.")
                    break
                
                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            print(f"Webcam (index {index}) closed.")
            user_input = input("Was this your built-in camera? (yes/no): ").lower()
            if user_input == "yes":
                print(f"\nSuccess: Built-in camera found at index {index}.")
                print("Update your main application to use cv2.VideoCapture(", index, ")")
                return index
        else:
            print(f"Failed to open webcam (index {index})")
            cap.release()
    
    print("\nError: Could not open any webcam or identify the built-in camera. Check the following:")
    print("- Ensure the webcam is connected and functioning.")
    print("- Check camera permissions (on macOS: System Settings > Privacy & Security > Camera).")
    print("- Ensure no other applications are using the webcam.")
    print("- Try different webcam indices if you have multiple cameras.")
    return None

if __name__ == "__main__":
    working_index = test_webcam()
    if working_index is not None:
        print(f"\nSuccess: Built-in camera works with index {working_index}.")
        print("Update your main application to use cv2.VideoCapture(", working_index, ")")
    else:
        print("\nFailed to find a working webcam.")
