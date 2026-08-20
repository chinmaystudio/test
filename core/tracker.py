import numpy as np

class SimpleTracker:
    """
    A very simple IoU-based tracker for demonstration.
    In production, replace with ByteTrack or DeepSORT.
    """
    def __init__(self, iou_threshold=0.3):
        self.tracks = {} # track_id -> dict
        self.next_id = 1
        self.iou_threshold = iou_threshold

    def _iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def update(self, detections):
        """
        detections: list of face objects with bbox
        Returns: list of (track_id, face)
        """
        updated_tracks = []
        unmatched_dets = list(detections)
        
        # Match existing tracks
        for track_id, track_info in list(self.tracks.items()):
            best_det_idx = -1
            best_iou = self.iou_threshold
            
            for i, det in enumerate(unmatched_dets):
                iou = self._iou(track_info['bbox'], det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = i
                    
            if best_det_idx >= 0:
                det = unmatched_dets.pop(best_det_idx)
                self.tracks[track_id]['bbox'] = det.bbox
                self.tracks[track_id]['hits'] += 1
                updated_tracks.append((track_id, det))
            else:
                self.tracks[track_id]['misses'] += 1
                if self.tracks[track_id]['misses'] > 5:
                    del self.tracks[track_id]
                    
        # New tracks
        for det in unmatched_dets:
            track_id = self.next_id
            self.next_id += 1
            self.tracks[track_id] = {'bbox': det.bbox, 'hits': 1, 'misses': 0}
            updated_tracks.append((track_id, det))
            
        return updated_tracks
