# Copyright (c) Facebook, Inc. and its affiliates.
# # Modified by Bowen Cheng from: https://github.com/facebookresearch/detr/blob/master/models/position_encoding.py
"""
Various positional encodings for the transformer.
"""
import math

import torch
from torch import nn


class PositionEmbeddingSine(nn.Module):
    """
    This is a more standard version of the position embedding, very similar to the one
    used by the Attention is all you need paper, generalized to work on images.
    """

    def __init__(
        self, num_pos_feats=64, temperature=10000, normalize=False, scale=None
    ):
        super().__init__()
        self.num_pos_feats = num_pos_feats
        self.temperature = temperature
        self.normalize = normalize
        if scale is not None and normalize is False:
            raise ValueError("normalize should be True if scale is passed")
        if scale is None:
            scale = 2 * math.pi
        self.scale = scale

    def forward(self, x, mask=None):
        if mask is None:
            mask = torch.zeros(
                (x.size(0), x.size(2), x.size(3), x.size(4)),
                device=x.device,
                dtype=torch.bool,
            )
        not_mask = ~mask

        x_embed = not_mask.cumsum(1, dtype=torch.float)
        y_embed = not_mask.cumsum(2, dtype=torch.float)
        z_embed = not_mask.cumsum(3, dtype=torch.float)

        if self.normalize:
            eps = 1e-6
            x_embed = x_embed / (x_embed[:, -1:, :, :] + eps) * self.scale
            y_embed = y_embed / (y_embed[:, :, -1:, :] + eps) * self.scale
            z_embed = z_embed / (z_embed[:, :, :, -1:] + eps) * self.scale

        dim_t = torch.arange(self.num_pos_feats, dtype=torch.float, device=x.device)
        dim_t = self.temperature ** (2 * (dim_t // 2) / self.num_pos_feats)

        pos_x = x_embed[:, :, :, :, None] / dim_t
        pos_y = y_embed[:, :, :, :, None] / dim_t
        pos_z = z_embed[:, :, :, :, None] / dim_t

        pos_x = torch.stack(
            (pos_x[:, :, :, :, 0::2].sin(), pos_x[:, :, :, :, 1::2].cos()), dim=4
        ).flatten(4)
        pos_y = torch.stack(
            (pos_y[:, :, :, :, 0::2].sin(), pos_y[:, :, :, :, 1::2].cos()), dim=4
        ).flatten(4)
        pos_z = torch.stack(
            (pos_z[:, :, :, :, 0::2].sin(), pos_z[:, :, :, :, 1::2].cos()), dim=4
        ).flatten(4)

        pos = torch.cat((pos_x, pos_y, pos_z), dim=4).permute(0, 4, 1, 2, 3)
        return pos


class PositionEmbeddingSineSparse(nn.Module):
    """
    This is a sparse version of the position embedding, very similar to the one
    used by the Attention is all you need paper, generalized to work on images.
    """

    def __init__(
        self, num_pos_feats=64, temperature=10000, normalize=False, scale=None
    ):
        super().__init__()
        self.num_pos_feats = num_pos_feats
        self.temperature = temperature
        self.normalize = normalize
        if scale is not None and normalize is False:
            raise ValueError("normalize should be True if scale is passed")
        if scale is None:
            scale = 2 * math.pi
        self.scale = scale

    def forward(self, coords):
        """
        coords: (N, 3) tensor of (x, y, z) coordinates
        """
        coords = coords.float()  # (N, 3)

        x_embed = coords[:, 0]  # (N, )
        y_embed = coords[:, 1]  # (N, )
        z_embed = coords[:, 2]  # (N, )

        if self.normalize:
            eps = 1e-6
            x_embed = x_embed / (x_embed + eps) * self.scale  # (N, )
            y_embed = y_embed / (y_embed + eps) * self.scale  # (N, )
            z_embed = z_embed / (z_embed + eps) * self.scale  # (N, )

        dim_t = torch.arange(
            self.num_pos_feats, dtype=torch.float, device=coords.device
        )  # (num_pos_feats, )
        dim_t = self.temperature ** (
            2 * (dim_t // 2) / self.num_pos_feats
        )  # (num_pos_feats, )

        pos_x = x_embed[:, None] / dim_t  # (N, num_pos_feats)
        pos_y = y_embed[:, None] / dim_t  # (N, num_pos_feats)
        pos_z = z_embed[:, None] / dim_t  # (N, num_pos_feats)

        pos_x = torch.stack(
            (pos_x[:, 0::2].sin(), pos_x[:, 1::2].cos()), dim=1
        ).flatten(
            1
        )  # (N, num_pos_feats)
        pos_y = torch.stack(
            (pos_y[:, 0::2].sin(), pos_y[:, 1::2].cos()), dim=1
        ).flatten(
            1
        )  # (N, num_pos_feats)
        pos_z = torch.stack(
            (pos_z[:, 0::2].sin(), pos_z[:, 1::2].cos()), dim=1
        ).flatten(
            1
        )  # (N, num_pos_feats)

        pos = torch.cat((pos_x, pos_y, pos_z), dim=1)  # (N, num_pos_feats * 3)

        return pos
