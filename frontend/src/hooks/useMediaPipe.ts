import { useEffect, useRef, useState } from "react";
import {
  FaceLandmarker,
  FilesetResolver,
} from "@mediapipe/tasks-vision";

export interface FaceMetrics {
  faceDetected: boolean;    // whether a face is visible
  eyeContact: boolean;
  lookingAway: boolean;
  blinkDetected: boolean;
  headPose: "center" | "nodding" | "tilted" | "turned";
  smileScore: number;
  mouthOpen: boolean;
  eyebrowRaise: boolean;
  status: "loading" | "ready" | "no_face" | "error";
}

const DEFAULT_METRICS: FaceMetrics = {
  faceDetected: false,
  eyeContact: false,
  lookingAway: false,
  blinkDetected: false,
  headPose: "center",
  smileScore: 0,
  mouthOpen: false,
  eyebrowRaise: false,
  status: "loading",
};

export function useMediaPipe(videoRef: React.RefObject<HTMLVideoElement>) {
  const [metrics, setMetrics] = useState<FaceMetrics>(DEFAULT_METRICS);
  const landmarkerRef = useRef<FaceLandmarker | null>(null);
  const animFrameRef = useRef<number>(0);
  const lastVideoTimeRef = useRef<number>(-1);

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        const filesetResolver = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        );
        const faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
          baseOptions: {
            modelAssetPath:
              "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
            delegate: "GPU",
          },
          outputFaceBlendshapes: true,
          runningMode: "VIDEO",
          numFaces: 1,
        });

        if (!cancelled) {
          landmarkerRef.current = faceLandmarker;
          setMetrics((m) => ({ ...m, status: "ready" }));
        }
      } catch {
        if (!cancelled) setMetrics((m) => ({ ...m, status: "error" }));
      }
    };

    init();
    return () => { cancelled = true; };
  }, []);

  // Start detection loop once video is playing
  useEffect(() => {
    const detect = () => {
      const video = videoRef.current;
      const landmarker = landmarkerRef.current;

      if (!video || !landmarker || video.readyState < 2) {
        animFrameRef.current = requestAnimationFrame(detect);
        return;
      }

      if (video.currentTime === lastVideoTimeRef.current) {
        animFrameRef.current = requestAnimationFrame(detect);
        return;
      }

      lastVideoTimeRef.current = video.currentTime;

      try {
        const result = landmarker.detectForVideo(video, performance.now());

        if (!result.faceLandmarks || result.faceLandmarks.length === 0) {
          setMetrics({ faceDetected: false, eyeContact: false, lookingAway: false, blinkDetected: false, headPose: "center", smileScore: 0, mouthOpen: false, eyebrowRaise: false, status: "ready" });
          animFrameRef.current = requestAnimationFrame(detect);
          return;
        }

        const landmarks = result.faceLandmarks[0];
        const blendshapes = result.faceBlendshapes?.[0]?.categories || [];

        const bs = (name: string) =>
          blendshapes.find((b) => b.categoryName === name)?.score ?? 0;

        // Eye contact: check if nose tip is roughly centered (landmarks[1])
        const noseTip = landmarks[1];
        const eyeContact = noseTip.x > 0.35 && noseTip.x < 0.65 && noseTip.y > 0.3 && noseTip.y < 0.7;
        const lookingAway = noseTip.x < 0.25 || noseTip.x > 0.75;

        // Blink: check eyeBlinkLeft blendshape score
        const blinkLeft = blendshapes.find((b) => b.categoryName === "eyeBlinkLeft");
        const blinkDetected = (blinkLeft?.score ?? 0) > 0.4;

        // Head pose using nose tip + chin (landmark 152) + left/right ear (234, 454)
        const chin = landmarks[152];
        const leftEar = landmarks[234];
        const rightEar = landmarks[454];
        const foreHead = landmarks[10]; // top of forehead
        const yaw = leftEar.z - rightEar.z;           // turning left/right
        const roll = leftEar.y - rightEar.y;          // tilting
        // Pitch: compare nose tip Y vs midpoint of forehead and chin
        const faceMidY = (foreHead.y + chin.y) / 2;
        const pitchOffset = noseTip.y - faceMidY;     // positive = looking down, negative = looking up
        let headPose: FaceMetrics["headPose"] = "center";
        if (Math.abs(yaw) > 0.08) headPose = "turned";
        else if (Math.abs(roll) > 0.06) headPose = "tilted";
        else if (pitchOffset < -0.04) headPose = "nodding"; // nose clearly above face midpoint = head tilted up/nodding

        // Smile: average of left + right smile blendshapes
        const smileScore = (bs("mouthSmileLeft") + bs("mouthSmileRight")) / 2;

        // Mouth open: jaw open blendshape
        const mouthOpen = bs("jawOpen") > 0.35;

        // Eyebrow raise: inner + outer brow up
        const eyebrowRaise = bs("browInnerUp") > 0.4 || bs("browOuterUpLeft") > 0.4 || bs("browOuterUpRight") > 0.4;

        setMetrics({ faceDetected: true, eyeContact, lookingAway, blinkDetected, headPose, smileScore, mouthOpen, eyebrowRaise, status: "ready" });
      } catch {
        // silently continue
      }

      animFrameRef.current = requestAnimationFrame(detect);
    };

    animFrameRef.current = requestAnimationFrame(detect);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [videoRef]);

  return metrics;
}
