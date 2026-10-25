"""Check model output compatibility without downloading pretrained weights."""

import pytest
import torch

from quran_muaalem.modeling.configuration_multi_level_ctc import Wav2Vec2BertForMultilevelCTCConfig
from quran_muaalem.modeling.modeling_multi_level_ctc import Wav2Vec2BertForMultilevelCTC


@pytest.mark.parametrize("hidden,attentions", [(False, False), (True, False), (False, True), (True, True)])
def test_tuple_matches_named_outputs(hidden, attentions):
    config = Wav2Vec2BertForMultilevelCTCConfig(
        hidden_size=8, num_hidden_layers=1, num_attention_heads=2,
        intermediate_size=16, feature_projection_input_dim=4,
        conv_depthwise_kernel_size=3, level_to_vocab_size={"phonemes": 5},
        apply_spec_augment=False, attn_implementation="eager",
    )
    model = Wav2Vec2BertForMultilevelCTC(config).eval()
    features = torch.randn(1, 12, 4)
    with torch.no_grad():
        named = model(features, output_hidden_states=hidden, output_attentions=attentions, return_dict=True)
        positional = model(features, output_hidden_states=hidden, output_attentions=attentions, return_dict=False)
    torch.testing.assert_close(positional[0]["phonemes"], named.logits["phonemes"])
    expected = [value for value in (named.hidden_states, named.attentions) if value is not None]
    assert len(positional) == 1 + len(expected)
    for actual, wanted in zip(positional[1:], expected):
        torch.testing.assert_close(actual, wanted)
