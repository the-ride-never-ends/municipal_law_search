import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from logger import logger 
from configs import configs


def _torch_cosine_similarity(x: list[float], y: list[float]) -> np.float64:
    """
    Compute the cosine similarity between two vectors using PyTorch.

    This function calculates the cosine similarity between two vectors, potentially
    leveraging GPU acceleration if available and configured.

    Args:
        x (torch.Tensor): The first vector for similarity calculation.
        y (torch.Tensor): The second vector for similarity calculation.

    Returns:
        np.float64: The cosine similarity value between the two vectors,
            with a range from -1 (completely opposite) to 1 (exactly the same).
    """
    # Convert lists to torch tensors
    x_tensor = torch.tensor(x, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32)

    # Move tensors to GPU if available
    device = torch.device(configs.USE_GPU_FOR_COSINE_SIMILARITY)
    x_tensor = x_tensor.to(device)
    y_tensor = y_tensor.to(device)

    # Calculate cosine similarity using torch
    return np.float64(
        torch.nn.functional.cosine_similarity(
            x_tensor, 
            y_tensor
        ).item()
    )

def _numpy_cosine_similarity(x: list[float], y: list[float]) -> np.float64:
    """
    Calculates the cosine similarity between two vectors using NumPy.

    Cosine similarity measures the cosine of the angle between two non-zero vectors,
    providing a value between -1 and 1 where 1 means identical vectors, 0 means
    orthogonal vectors, and -1 means exactly opposite vectors.

    Args:
        x: First vector represented as a list of floats.
        y: Second vector represented as a list of floats.

    Returns:
        The cosine similarity between vectors x and y as a numpy float64.

    """
    return np.dot(
        np.array(x), np.array(y)
            ) / (
        np.linalg.norm(np.array(x)) * np.linalg.norm(np.array(y))
    )

def cosine_similarity(x: list[float], y: list[float]) -> np.float64:
    """
    Calculate cosine similarity between two vectors.

    Args:
        x: First vector
        y: Second vector

    Returns:
        Cosine similarity score, ranging from -1 to 1.
            - 1 indicates identical vectors, 
            - 0 indicates orthogonal (e.g. perpendicular) vectors
            - -1 indicates opposite vectors.
    """
    if TORCH_AVAILABLE and configs.USE_GPU_FOR_COSINE_SIMILARITY == "cuda":
        return _torch_cosine_similarity(x, y)
    else:
        return _numpy_cosine_similarity(x, y)
