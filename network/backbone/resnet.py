import torch
import torch.nn as nn
try:  # for torchvision<0.4
    from torchvision.models.utils import load_state_dict_from_url
except:  # for torchvision>=0.4
    from torch.hub import load_state_dict_from_url


__all__ = ['ResNet', 'resnet18', 'resnet34', 'resnet50', 'resnet101',
           'resnet152', 'resnext50_32x4d', 'resnext101_32x8d',
           'wide_resnet50_2', 'wide_resnet101_2']


model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
    'resnext50_32x4d': 'https://download.pytorch.org/models/resnext50_32x4d-7cdf4587.pth',
    'resnext101_32x8d': 'https://download.pytorch.org/models/resnext101_32x8d-8ba56ff5.pth',
    'wide_resnet50_2': 'https://download.pytorch.org/models/wide_resnet50_2-95faca4d.pth',
    'wide_resnet101_2': 'https://download.pytorch.org/models/wide_resnet101_2-32ee1156.pth',
}


def conv7x7(in_planes, out_planes, stride=1, groups=1, dilation=1):
    """7x7 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=7, stride=stride,
                     padding=3 * dilation, groups=groups, bias=False, dilation=dilation)


def conv5x5(in_planes, out_planes, stride=1, groups=1, dilation=1):
    """5x5 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=5, stride=stride,
                     padding=2 * dilation, groups=groups, bias=False, dilation=dilation)


def conv3x3(in_planes, out_planes, stride=1, groups=1, dilation=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=dilation, groups=groups, bias=False, dilation=dilation)


def conv1x1(in_planes, out_planes, stride=1):
    """1x1 convolution"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None, groups=1,
                 base_width=64, dilation=1, norm_layer=None):
        super(BasicBlock, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        if groups != 1 or base_width != 64:
            raise ValueError('BasicBlock only supports groups=1 and base_width=64')
        #if dilation > 1:
        #    raise NotImplementedError("Dilation > 1 not supported in BasicBlock")
        # Both self.conv1 and self.downsample layers downsample the input when stride != 1
        self.conv1 = conv3x3(inplanes, planes, stride, dilation=dilation)
        self.bn1 = norm_layer(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes, dilation=dilation)
        self.bn2 = norm_layer(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)

        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None, groups=1,
                 base_width=64, dilation=1, norm_layer=None):
        super(Bottleneck, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        width = int(planes * (base_width / 64.)) * groups
        # Both self.conv2 and self.downsample layers downsample the input when stride != 1
        self.conv1 = conv1x1(inplanes, width)
        self.bn1 = norm_layer(width)
        self.conv2 = conv3x3(width, width, stride, groups, dilation)
        self.bn2 = norm_layer(width)
        self.conv3 = conv1x1(width, planes * self.expansion)
        self.bn3 = norm_layer(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)

        return out


class StemBlock3(nn.Module):
    def __init__(self, inplanes=3, planes=[64, 64], strides=[1, 2]):
        super().__init__()
        self.conv1 = conv3x3(inplanes, planes[0], stride=strides[0])
        self.bn1 = nn.BatchNorm2d(planes[0])

        self.conv2 = conv3x3(inplanes, planes[1], stride=strides[1])
        self.bn2 = nn.BatchNorm2d(planes[1])

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(x)
        out = self.bn2(out)
        out = self.relu(out)
        return out


class StemBlock1(nn.Module):
    def __init__(self, inplanes, planes, stride=1):
        super().__init__()
        self.conv1 = conv3x3(inplanes, planes[0], stride=stride)
        self.bn1 = nn.BatchNorm2d(planes[0])

        self.conv2 = conv5x5(inplanes, planes[1], stride=stride)
        self.bn2 = nn.BatchNorm2d(planes[1])

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out_1 = self.conv1(x)
        out_1 = self.bn1(out_1)

        out_2 = self.conv2(x)
        out_2 = self.bn2(out_2)

        out = torch.cat([out_1, out_2], dim=1)
        return self.relu(out)


class StemBlock2(nn.Module):
    def __init__(self, inplanes, planes, stride=2, channel_reduction=16, dilation=1):
        super().__init__()
        self.conv1 = conv1x1(inplanes, planes[0], stride=stride)
        self.bn1 = nn.BatchNorm2d(planes[0])

        self.conv2_1 = conv1x1(inplanes, channel_reduction)
        self.conv2_2 = conv3x3(channel_reduction, planes[1], stride=stride)
        self.bn2 = nn.BatchNorm2d(planes[1])

        self.conv3_1 = conv1x1(inplanes, channel_reduction)
        self.conv3_2 = conv5x5(channel_reduction, planes[2], stride=stride)
        self.bn3 = nn.BatchNorm2d(planes[2])

        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=stride, padding=1)
        self.conv4 = conv1x1(inplanes, planes[3])
        self.bn4 = nn.BatchNorm2d(planes[3])

        self.relu = nn.ReLU(inplace=True)
        self.stride = stride
        self.downsample = nn.Sequential(
                            conv1x1(inplanes, sum(planes), stride=stride),
                            nn.BatchNorm2d(sum(planes))
                            )

        self.conv5 = conv1x1(sum(planes), 64, stride=1)
        self.bn5 = nn.BatchNorm2d(64)

    def forward(self, x):
        identity = x

        out_1 = self.conv1(x)
        out_1 = self.bn1(out_1)

        out_2 = self.conv2_1(x)
        out_2 = self.conv2_2(out_2)
        out_2 = self.bn2(out_2)

        out_3 = self.conv3_1(x)
        out_3 = self.conv3_2(out_3)
        out_3 = self.bn3(out_3)

        out_4 = self.maxpool(x)
        out_4 = self.conv4(out_4)
        out_4 = self.bn4(out_4)

        out = torch.cat([out_1, out_2, out_3, out_4], dim=1)
        out += self.downsample(identity)
        out = self.relu(out)

        out = self.conv5(out)
        out = self.bn5(out)
        return self.relu(out)


class RichStem(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.block1 = StemBlock1(3, [32, 32], stride=1)
        self.block2 = StemBlock2(64, [32, 64, 64, 32], channel_reduction=16, stride=2)

    def forward(self, x):
        out = self.block1(x)
        return self.block2(out)


class ClassicStem(nn.Module):
    def __init__(self, inplanes=64, fl_stemstride=True, **kwargs):
        super().__init__()
        stem_stride = 2 if fl_stemstride else 1
        self.conv1 = nn.Conv2d(3, inplanes, kernel_size=7, stride=stem_stride, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(inplanes)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        return self.relu(x)


class ParallelStem(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.classic = ClassicStem()
        #self.rich = RichStem()
        self.rich = StemBlock3()

    def forward(self, x):
        return self.classic(x) + self.rich(x)


class ResNet(nn.Module):
    def __init__(self, block, layers, num_classes=1000, zero_init_residual=False,
                 groups=1, width_per_group=64, replace_stride_with_dilation=None,
                 norm_layer=None, fl_maxpool=True, fl_richstem=False, fl_parallelstem=False,
                 fl_stemstride=True, fl_lfe=False, output_stride_diff=8, **kwargs):

        assert not fl_richstem or not fl_parallelstem, \
               "Or set fl_richstem or fl_richstem_parallel, but not both"

        super(ResNet, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        self._norm_layer = norm_layer

        self.inplanes = 64
        self.fl_lfe = fl_lfe
        self.output_stride_diff = output_stride_diff
        self.dilation = 1
        self.fl_maxpool = fl_maxpool
        self.fl_richstem = fl_richstem
        self.fl_parallelstem = fl_parallelstem
        if replace_stride_with_dilation is None:
            # each element in the tuple indicates if we should replace
            # the 2x2 stride with a dilated convolution instead
            replace_stride_with_dilation = [False, False, False]
        if len(replace_stride_with_dilation) != 3:
            raise ValueError("replace_stride_with_dilation should be None "
                             "or a 3-element tuple, got {}".format(replace_stride_with_dilation))
        self.groups = groups
        self.base_width = width_per_group

        if fl_parallelstem:
            self.stem = ParallelStem()
        else:
            self.stem = RichStem() if fl_richstem else ClassicStem(fl_stemstride=fl_stemstride)

        if self.fl_maxpool:
            self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2, block_id=2, dilate=replace_stride_with_dilation[0])
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2, block_id=3, dilate=replace_stride_with_dilation[1])
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2, block_id=4, dilate=replace_stride_with_dilation[2])
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * block.expansion, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, (nn.BatchNorm2d, nn.GroupNorm)):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

        # Zero-initialize the last BN in each residual branch,
        # so that the residual branch starts with zeros, and each residual block behaves like an identity.
        # This improves the model by 0.2~0.3% according to https://arxiv.org/abs/1706.02677
        if zero_init_residual:
            for m in self.modules():
                if isinstance(m, Bottleneck):
                    nn.init.constant_(m.bn3.weight, 0)
                elif isinstance(m, BasicBlock):
                    nn.init.constant_(m.bn2.weight, 0)

    def _make_layer(self, block, planes, blocks, stride=1, dilate=False, block_id=None):
        if self.fl_lfe and block_id is not None:
            assert block_id in [2, 3, 4], 'LFE is only used in the blocks 2, 3, 4.'
            if block_id == 2:
                lfe_factors = [1, 2, 2, 1]
            elif block_id == 3:
                lfe_factors = [1, 2, 3, 3, 2, 1]
            elif block_id == 4:
                lfe_factors = [1, 2, 1]

        norm_layer = self._norm_layer
        downsample = None
        previous_dilation = self.dilation

        if dilate:
            if self.fl_lfe and block_id > 2:
                if block_id == 3:
                    self.dilation = self.output_stride_diff / self.dilation
                elif self.dilation > 1:
                    self.dilation /= stride
                else:
                    pass
            else:
                self.dilation *= stride
            stride = 1

        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(self.inplanes, planes * block.expansion, stride),
                norm_layer(planes * block.expansion),
            )

        list_dilations = []
        if self.fl_lfe and block_id is not None:
            for f in lfe_factors:
                if f == 1:
                    list_dilations.append(1)
                elif f == 2:
                    list_dilations.append(self.dilation)
                elif f == 3:
                    list_dilations.append(2 * self.dilation - 1)
        else:
            list_dilations = [previous_dilation]
            list_dilations.extend([self.dilation for _ in range(1, blocks)])

        list_dilations = [int(d) for d in list_dilations]

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample, self.groups,
                            self.base_width, list_dilations[0], norm_layer))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, groups=self.groups,
                                base_width=self.base_width, dilation=list_dilations[i],
                                norm_layer=norm_layer))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.stem(x)
        if self.fl_maxpool:
            x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)

        return x


def _resnet(arch, block, layers, pretrained, progress, **kwargs):
    model = ResNet(block, layers, **kwargs)

    if pretrained:
        state_dict = load_state_dict_from_url(model_urls[arch],
                                              progress=progress)

        # Change names to use the classic stem 7x7s2
        # Otherwise train stem from scratch with strict=False
        if not kwargs.get('fl_richstem') and not kwargs.get('fl_parallelstem'):
            for k in list(state_dict.keys()):
                if k in ['conv1.weight', 'bn1.weight', 'bn1.bias',
                         'bn1.running_mean', 'bn1.running_var']:
                    state_dict['stem.{}'.format(k)] = state_dict.pop(k)
        elif kwargs.get('fl_parallelstem'):
            for k in list(state_dict.keys()):
                if k in ['conv1.weight', 'bn1.weight', 'bn1.bias',
                         'bn1.running_mean', 'bn1.running_var']:
                    state_dict['stem.classic.{}'.format(k)] = state_dict.pop(k)

        model.load_state_dict(state_dict, strict=False)
    return model


def resnet18(pretrained=False, progress=True, **kwargs):
    r"""ResNet-18 model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    return _resnet('resnet18', BasicBlock, [2, 2, 2, 2], pretrained, progress,
                   **kwargs)


def resnet34(pretrained=False, progress=True, **kwargs):
    r"""ResNet-34 model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    return _resnet('resnet34', BasicBlock, [3, 4, 6, 3], pretrained, progress,
                   **kwargs)


def resnet50(pretrained=False, progress=True, **kwargs):
    r"""ResNet-50 model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    return _resnet('resnet50', Bottleneck, [3, 4, 6, 3], pretrained, progress,
                   **kwargs)


def resnet101(pretrained=False, progress=True, **kwargs):
    r"""ResNet-101 model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    return _resnet('resnet101', Bottleneck, [3, 4, 23, 3], pretrained, progress,
                   **kwargs)


def resnet152(pretrained=False, progress=True, **kwargs):
    r"""ResNet-152 model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    return _resnet('resnet152', Bottleneck, [3, 8, 36, 3], pretrained, progress,
                   **kwargs)


def resnext50_32x4d(pretrained=False, progress=True, **kwargs):
    r"""ResNeXt-50 32x4d model from
    `"Aggregated Residual Transformation for Deep Neural Networks" <https://arxiv.org/pdf/1611.05431.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    kwargs['groups'] = 32
    kwargs['width_per_group'] = 4
    return _resnet('resnext50_32x4d', Bottleneck, [3, 4, 6, 3],
                   pretrained, progress, **kwargs)


def resnext101_32x8d(pretrained=False, progress=True, **kwargs):
    r"""ResNeXt-101 32x8d model from
    `"Aggregated Residual Transformation for Deep Neural Networks" <https://arxiv.org/pdf/1611.05431.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    kwargs['groups'] = 32
    kwargs['width_per_group'] = 8
    return _resnet('resnext101_32x8d', Bottleneck, [3, 4, 23, 3],
                   pretrained, progress, **kwargs)


def wide_resnet50_2(pretrained=False, progress=True, **kwargs):
    r"""Wide ResNet-50-2 model from
    `"Wide Residual Networks" <https://arxiv.org/pdf/1605.07146.pdf>`_

    The model is the same as ResNet except for the bottleneck number of channels
    which is twice larger in every block. The number of channels in outer 1x1
    convolutions is the same, e.g. last block in ResNet-50 has 2048-512-2048
    channels, and in Wide ResNet-50-2 has 2048-1024-2048.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    kwargs['width_per_group'] = 64 * 2
    return _resnet('wide_resnet50_2', Bottleneck, [3, 4, 6, 3],
                   pretrained, progress, **kwargs)


def wide_resnet101_2(pretrained=False, progress=True, **kwargs):
    r"""Wide ResNet-101-2 model from
    `"Wide Residual Networks" <https://arxiv.org/pdf/1605.07146.pdf>`_

    The model is the same as ResNet except for the bottleneck number of channels
    which is twice larger in every block. The number of channels in outer 1x1
    convolutions is the same, e.g. last block in ResNet-50 has 2048-512-2048
    channels, and in Wide ResNet-50-2 has 2048-1024-2048.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
    """
    kwargs['width_per_group'] = 64 * 2
    return _resnet('wide_resnet101_2', Bottleneck, [3, 4, 23, 3],
                   pretrained, progress, **kwargs)
